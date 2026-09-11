import pytest
from backend.ingestion.country_assigner import assign_location

def test_assign_canada_provinces():
    # British Columbia
    bc = assign_location(49.2827, -123.1207, "canada")
    assert bc["country_code"] == "CA"
    assert "British Columbia" in bc["province"]

    # Yukon
    yt = assign_location(60.7212, -135.0568, "canada")
    assert yt["country_code"] == "CA"
    assert "Yukon" in yt["province"]

def test_assign_us_in_canada_sector():
    # Gillette, Wyoming
    wy = assign_location(43.7742, -105.3225, "canada")
    assert wy["country_code"] == "US"
    assert wy["country_name"] == "United States"
    assert wy["province"] == "Wyoming"

    # Minnesota
    mn = assign_location(47.5595, -92.6648, "canada")
    assert mn["country_code"] == "US"
    assert mn["province"] == "Minnesota"

def test_assign_china_provinces():
    # Sichuan
    sc = assign_location(30.6586, 104.0648, "china")
    assert sc["country_code"] == "CN"
    assert sc["country_name"] == "China"
    assert sc["province"] == "Sichuan"

    # Xinjiang
    xj = assign_location(41.7724, 81.0795, "china")
    assert xj["country_code"] == "CN"
    assert xj["province"] == "Xinjiang"

def test_assign_neighboring_nations_in_china_sector():
    # Japan (Matsue, Honshu)
    jp = assign_location(35.3273, 133.0704, "china")
    assert jp["country_code"] == "JP"
    assert jp["country_name"] == "Japan"

    # Russia (Lake Baikal area)
    ru = assign_location(51.5000, 107.0000, "china")
    assert ru["country_code"] == "RU"

    # Mongolia (Ulaanbaatar)
    mng = assign_location(47.9212, 106.9186, "china")
    assert mng["country_code"] == "MN"

def test_assign_offshore():
    # Deep Pacific Ocean
    ofs = assign_location(26.8062, 130.0648, "china")
    assert ofs["country_code"] == "OFS"
    assert ofs["country_name"] == "Offshore"
