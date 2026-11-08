import json
import pandas as pd
import pytest
from dataflow_automation import run_pipeline
from dataflow_automation.cleaning import clean
from dataflow_automation.io import DataflowError, read_table
from dataflow_automation.cli import main


def csv(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_mixed_formats_and_accounting(tmp_path):
    a = csv(tmp_path, "a.csv", "Código,Produto,Quantidade\n001, Caneta ,2\n002,Papel,bad\n003, ,1\n")
    b = tmp_path / "b.xlsx"
    pd.DataFrame({"Código": ["001", "004"], "Produto": ["Caneta", "Lapis"], "Quantidade": ["2", "5"]}).to_excel(b, index=False)
    output = tmp_path / "out.xlsx"
    report = run_pipeline([a, b], output, required=["codigo", "produto"], numeric=["quantidade"])
    assert report["rows_read"] == 5
    assert report["invalid_rows"] == 2
    assert report["duplicates_removed"] == 1
    assert report["rows_written"] == 2
    assert read_table(output)["codigo"].tolist() == ["001", "004"]
    assert json.loads(output.with_suffix(".report.json").read_text())["rows_written"] == 2
    assert "numeric:quantidade" in output.with_suffix(".rejected.csv").read_text()


def test_blank_rows_and_literal_na():
    frame = clean(pd.DataFrame({" Nome ": ["  ", " NA ", None]}))
    assert frame["nome"].tolist() == ["NA"]


@pytest.mark.parametrize("headers", [["A B", "A-B"], ["!!!"], ["df_source"]])
def test_invalid_headers(headers):
    with pytest.raises(DataflowError):
        clean(pd.DataFrame([["x"]*len(headers)], columns=headers))


def test_schema_checked_for_each_file(tmp_path):
    a = csv(tmp_path, "a.csv", "id,name\n1,A\n")
    b = csv(tmp_path, "b.csv", "id\n2\n")
    with pytest.raises(DataflowError, match="Missing configured"):
        run_pipeline([a, b], tmp_path / "out.csv", required=["name"])
    assert not (tmp_path / "out.csv").exists()


def test_union_and_key_deduplication(tmp_path):
    a = csv(tmp_path, "a.csv", "id,name\n01,A\n01,B\n")
    b = csv(tmp_path, "b.csv", "id,extra\n02,C\n")
    report = run_pipeline([a, b], tmp_path / "out.csv", dedupe_on=["id"])
    assert report["rows_written"] == 2
    assert report["duplicates_removed"] == 1
    assert "extra" in read_table(tmp_path / "out.csv").columns


def test_output_protection(tmp_path):
    a = csv(tmp_path, "a.csv", "id\n1\n")
    with pytest.raises(DataflowError, match="overwrite inputs"):
        run_pipeline([a], a, overwrite=True)
    output = tmp_path / "out.csv"
    run_pipeline([a], output)
    with pytest.raises(DataflowError, match="already exist"):
        run_pipeline([a], output)
    run_pipeline([a], output, overwrite=True)


@pytest.mark.parametrize("text", ["id\ninf\n", "id\n-Infinity\n", "id\nbad\n"])
def test_nonfinite_numbers_rejected(tmp_path, text):
    a = csv(tmp_path, "a.csv", text)
    assert run_pipeline([a], tmp_path / "out.csv", numeric=["id"])["invalid_rows"] == 1


def test_formula_export_neutralized(tmp_path):
    a = csv(tmp_path, "a.csv", "value\n=1+1\n")
    output = tmp_path / "out.xlsx"
    run_pipeline([a], output)
    import openpyxl
    cell = openpyxl.load_workbook(output).active["A2"]
    assert cell.data_type != "f"
    assert cell.value == "'=1+1"


@pytest.mark.parametrize("scenario", ["empty", "repeated", "missing", "unsupported", "dedupe"])
def test_invalid_inputs(tmp_path, scenario):
    a = csv(tmp_path, "a.csv", "id\n1\n")
    inputs = {"empty": [], "repeated": [a, a], "missing": [tmp_path / "missing.csv"],
              "unsupported": [tmp_path / "data.txt"], "dedupe": [a]}[scenario]
    with pytest.raises(DataflowError):
        run_pipeline(inputs, tmp_path / "out.csv", dedupe_on=["unknown"] if scenario == "dedupe" else None)


def test_delimiter_and_cli(tmp_path, capsys):
    a = csv(tmp_path, "a.csv", "id;name\n001; Demo \n")
    assert main([str(a), "-o", str(tmp_path / "out.csv"), "--delimiter", ";", "--required", "name"]) == 0
    assert '"rows_written": 1' in capsys.readouterr().out
    assert main(["missing.csv", "-o", str(tmp_path / "new.csv")]) == 1
    assert "Cannot read" in capsys.readouterr().err


def test_corrupt_excel_cli(tmp_path, capsys):
    a = csv(tmp_path, "broken.xlsx", "not an excel workbook")
    assert main([str(a), "-o", str(tmp_path / "out.csv")]) == 1
    assert "Cannot read" in capsys.readouterr().err
