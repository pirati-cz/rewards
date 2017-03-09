Česká pirátská strana  
{TMPTEAM}

Osobní výkaz odměňování
=======================

V tomtu výkazu zveřejňujeme základní informace o vykonané práci a odměňování
podle určité smlouvy. Výkaz je sestaven podle [metodiky odměňování][metodika],
která obsahuje podrobnosti. U všech údajů jsou uvedeny odkazy do projektového
systému [redmine](https://redmine.pirati.cz). Upozorňujeme, že za podmínek
stanovených v metodice mohou být některé úkoly v projektovém systému neveřejné.

Odměňovaný
----------

Jméno a příjmení:                      | {TMPNAME}
-----------------------                | --------------------
Funkce:                                | {TMPFUNCTION}
Tým:                                   | {TMPTEAM}
Smlouva:                               | {TMPCONTRACT}
Období:                                | {TMPTIMERANGE}


Odvedená práce
--------------

### Významné úkoly

Následující seznam zahrnuje všechny úkoly, které zabraly déle než 3 hodiny.

{TMPTASKS}

Můžete si zobrazit plný [přehled plněných úkolů][tasklist].
Slovní hodnocení je ve [zvláštním úkolu][hodnoceni].


### Počet hodin

Následující tabulka obsahuje měřitelné ukazatele za všechny úkoly v daném měsíci
včetně neveřejných úkolů. Proto mohou být hodiny v ní vyšší, než se vám bez
přihlášení zobrazí v projektovém systému.

Rozsah činnosti                        | Počet hodin
--------------                         | ----------:
Odhadnutý rozsah práce                 | {TMP_SMLUVNI_HODINY:6.2f} hod/týdně = {TMP_SMLUVNI_ODHAD_MESICNE:6.2f} hod/měs.
Skutečně odvedená práce dle smlouvy    | {TMP_SKUTECNA_PRACE:6.2f} hod
Práce hrazená jinými subjekty          | {TMP_SKUTECNA_REFUNDOVANA_PRACE:6.2f} hod
**Celkový počet hodin**                | {TMP_SKUTECNE_HODINY_CELKEM:6.2f} hod
**Procento vytížení**                  | {TMP_SKUTECNE_PROCENTO:4.0f} %

Odměna
------

Částky jsou uváděny vždy v hrubé výši. Je odpovědností každého příjemce, aby
příjem zdanil a zaplatil zákonné pojištění, pokud je nehradí plátce.

### Dohodnutý rozsah odměny

Složka smluvní odměny                  | Dohodnutá částka
----------------                       | ------------------:
Paušální odměna                        | {TMP_SMLUVNI_PAUSAL:8.2f} Kč
Hodinová odměna                        | {TMP_SMLUVNI_HODINOVKA:8.2f} Kč/hod
Úkolová odměna                         | {TMP_SMLUVNI_UKOLOVKA:8.2f} Kč
Odpočet                                | {TMP_SMLUVNI_ODPOCET:8.2f} Kč

### Skutečná odměna podle odvedené práce

Složka skutečné odměny                 | Skutečná odměna (Kč)
---------------------                  | ---------------------:
Paušální odměna                        | {TMP_SKUTECNY_PAUSAL:8.2f} Kč
Hodinová odměna do odhadnutého rozsahu | {TMP_SKUTECNA_HODINOVKA_POD:8.2f} Kč
Hodinová odměna nad odhadnutý rozsah   | {TMP_SKUTECNA_HODINOVKA_NAD:8.2f} Kč
Úkolová odměna                         | {TMP_SKUTECNA_UKOLOVKA:8.2f} Kč
Mimořádná odměna                       | {TMP_SKUTECNA_MIMORADNA_ODMENA:8.2f} Kč
Odpočet                                | {TMP_SKUTECNY_ODPOCET:8.2f} Kč
**Celková odměna**                     | {TMP_SKUTECNA_ODMENA_CELKEM:8.2f} Kč


### Odměna od jiných subjektů

{TMPREFUNDS}


Prohlášení o zdrojových datech
------------------------------

Tento výkaz byl vygenerován na základě následujících dat, které jsou jeho součástí:

* [Přehled plněných úkolů v daném období](user_report.csv)

[hodnoceni]: {TMP_HODNOCENI}
[metodika]: https://redmine.pirati.cz/projects/po/wiki/Odmenovani
{TMPLINKS}
