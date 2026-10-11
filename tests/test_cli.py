"""The hla-sero command, end to end (fake GitHub)."""

from hla_sero.cli import main


def test_convert_file_table(home, github, tmp_path, capsys):
    f = tmp_path / "typing.txt"
    f.write_text("S1\tB*15:03\tC*03:04\n")
    assert main(["convert", str(f)]) == 0
    out = capsys.readouterr().out
    assert "IPD-IMGT/HLA 9.99.0" in out and "B72" in out and "Cw10" in out


def test_convert_to_csv(home, github, tmp_path):
    f, out = tmp_path / "t.txt", tmp_path / "out.csv"
    f.write_text("S1 A*02:01\n")
    assert main(["convert", str(f), "-o", str(out)]) == 0
    lines = out.read_text().splitlines()
    assert lines[0].startswith("# IPD-IMGT/HLA 9.99.0")
    assert lines[1].startswith("line,sample,input,equivalent")
    assert ",A*02:01,A2," in lines[2]


def test_no_alleles_found(home, github, tmp_path):
    f = tmp_path / "t.txt"
    f.write_text("nothing here")
    assert main(["convert", str(f)]) == 1


def test_config_and_status(home, github, capsys):
    assert main(["config", "--auto-update", "notify"]) == 0
    assert "Auto-update   : notify" in capsys.readouterr().out


def test_demo_is_synthetic(capsys):
    main(["demo", "-n", "2"])
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 2 and out[0].startswith("SYN0001\t")
