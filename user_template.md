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

Jméno a příjmení:        | {TMPNAME}
-----------------------  | --------------------
Funkce:                  | {TMPFUNCTION}
Tým:                     | {TMPTEAM}
Smlouva:                 | {TMPCONTRACT}
Období:                  | {TMPTIMERANGE}
Odměna dle smlouvy:      | {TMPMONEYRANGE}

Odvedená práce
--------------

### Odpracovaný čas

Následující seznam zahrnuje všechny úkoly, které zabraly déle než 3 hodiny.

{TMPTASKS}

Můžete si zobrazit plný [přehled plněných úkolů][tasklist].

### Měřitelné ukazatele

Následující tabulka obsahuje měřitelné ukazatele za všechny úkoly v daném měsíci
včetně neveřejných úkolů. Proto mohou být hodiny v ní vyšší než se vám bez
přihlášení zobrazí v projektovém systému.

Rozsah činnosti                        | Počet hodin
--------------                         | ----------:
A. Práce hrazená dle smlouvy           | {TMPPARTYHOURS:6.2f}
B. Práce hrazená jinými subjekty       | {TMPCITYHOURS:6.2f}
**Celkový počet hodin**                | {TMPTOTALHOURS:6.2f}
Dohodnutý rozsah práce                 | {TMPNORM:6.2f}
**Procento vytížení**                  | {TMPPERCENTAGE:4.0f} %

Odměna
------

Částky jsou uváděny vždy v hrubé výši. Je odpovědností každého příjemce, aby
příjem zdanil a zaplatil zákonné pojištění, pokud je nehradí plátce.

### Odměna dle smlouvy

Složka příjmu                   | Přiznaná částka (Kč)
-----------------               | --------------------:
A.1 Pevná složka                | {TMPCONSTMONEY:8.2f}
A.2 Variabilní složka           | {TMPVARMONEY:8.2f}
*z toho*                        |
A.2.1 Odměna za splněné úkoly   | {TMPTASKSMONEY:8.2f}
A.2.2 Odpočet za výhrady        | {TMPSANCTIONS:8.2f}
A.2.3 Odměna nad rámec smlouvy  | {TMPOVERTIMEMONEY:8.2f}
**Celková odměna**              | {TMPPARTYMONEY:8.2f}

{TMPMONEYCOMMENT}

### Odměna od jiných subjektů

{TMPREFUNDS}


Prohlášení o zdrojových datech
------------------------------

Tento výkaz byl vygenerován na základě následujících dat, které jsou jeho součástí:

* [Přehled plněných úkolů v daném období](user_report.csv)
* [Stanovení úkolových odměn v týmu](../task_rewards.csv)

[metodika]: https://redmine.pirati.cz/projects/praha/wiki/Odm%C4%9B%C5%88ov%C3%A1n%C3%AD_zastupitel%C5%AF
{TMPLINKS}
