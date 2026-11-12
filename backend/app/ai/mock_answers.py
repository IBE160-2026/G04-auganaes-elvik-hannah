"""Canned answers for the mock provider (Story 5.1, FR-22, AD-15), one per catalog type.

Norwegian only. tests/test_ai.py checks that every catalog type has one. They are task-specific,
not right for every home: the disclaimer travels with them like any other answer.
"""

BY_TASK_TYPE: dict[str, str] = {
    "vask-badet": (
        "Start med å fjerne løse ting. Spray et mildt baderomsmiddel på fliser og vask, la det "
        "virke noen minutter, og vask av med børste. Skyll godt og tørk av speil og kraner."
    ),
    "rens-sluket": (
        "Fjern hår og smuss fra rista for hånd, med hansker. Skyll med varmt vann. Bruk "
        "en sluktrekker eller en gammel tannbørste til det du ikke rekker."
    ),
    "kjokkenviftefilter": (
        "Slå av viften og ta ut filteret. La det ligge i varmt vann med oppvaskmiddel en stund, "
        "skrubb forsiktig, skyll og la det tørke helt før du setter det på plass igjen."
    ),
    "avkalk-vannkoker": (
        "Fyll vannkokeren halvfull med vann og en dæsj sitronsyre eller eddik, kok opp og la den "
        "stå en halvtime. Hell ut, skyll to ganger og kok opp rent vann én gang før bruk."
    ),
    "bak-kjoleskapet": (
        "Dra ut kjøleskapet og trekk ut støpselet først. Støvsug baksiden og gulvet bak, "
        "tørk av med en fuktig klut, og sett det på plass igjen."
    ),
    "stekeovn": (
        "La ovnen kjøle seg ned. Ta ut rister og plater. Stryk på et ovnsrens og følg "
        "tiden på pakken, eller bruk natron og vann til en pasta. Tørk av og skyll godt."
    ),
    "gulv": (
        "Støvsug først, slik at du ikke fordeler smuss. Vask deretter med en nesten tørr mopp "
        "og et mildt middel som passer til gulvtypen. Tre og laminat tåler lite vann."
    ),
    "dusjfuger": (
        "Spray fugene med et mildt middel mot kalk og mugg og la det virke. Skrubb med en "
        "fugebørste, skyll godt og tørk. Bland aldri flere rengjøringsmidler."
    ),
}

GENERIC = (
    "Ta det steg for steg: finn ut hva som skal gjøres rent, bruk et mildt middel først, test "
    "på et lite sted, og skyll og tørk godt etterpå."
)


def answer_for(task_type: str | None) -> str:
    return BY_TASK_TYPE.get(task_type, GENERIC) if task_type is not None else GENERIC
