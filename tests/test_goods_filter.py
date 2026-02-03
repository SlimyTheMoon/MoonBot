import logging


def test_filter_dict_keeps_allowed():
    import main as m

    m.ALLOWED_STATIONS = {"station_1"}
    data = {"station_1": {"a": 1}, "other": {"b": 2}}
    out = m._filter_goods_for_allowed_stations(data)
    assert out == {"station_1": {"a": 1}}


def test_filter_list_detects_station_field():
    import main as m

    m.ALLOWED_STATIONS = {"alpha"}
    data = [{"station": "alpha", "v": 1}, {"station": "beta", "v": 2}]
    out = m._filter_goods_for_allowed_stations(data)
    assert out == [{"station": "alpha", "v": 1}]


def test_unknown_shape_returns_original_and_logs(caplog):
    import main as m

    m.ALLOWED_STATIONS = {"x"}
    data = 12345
    with caplog.at_level(logging.WARNING):
        out = m._filter_goods_for_allowed_stations(data)
        assert out == data
        assert "Unknown goods payload shape" in caplog.text
