def get_sector_info(ticker):
    mapping = {
        "PKO.WA": ("WIG-BANKI.WA", "Banki"),
        "PEO.WA": ("WIG-BANKI.WA", "Banki"),
        "SPL.WA": ("WIG-BANKI.WA", "Banki"),
        "KGH.WA": ("WIG-GORNIC.WA", "Górnictwo"),
        "JSW.WA": ("WIG-GORNIC.WA", "Górnictwo"),
        "PKN.WA": ("WIG-PALIWA.WA", "Paliwa"),
        "PGE.WA": ("WIG-ENERG.WA", "Energetyka"),
        "TPE.WA": ("WIG-ENERG.WA", "Energetyka"),
        "DNP.WA": ("WIG-SPOZYW.WA", "Spożywczy"),
        "ALE.WA": ("WIG-SPOZYW.WA", "Handel"),
        "LPP.WA": ("WIG-ODZIEZ.WA", "Odzież")
    }
    return mapping.get(ticker, ("^WIG20", "Szeroki Rynek (WIG20)"))




## TODO: benchmark!!!!