
# WIP

## AHB Seitenanzahl pro Format

| Format       | Seitenanzahl | Hinweis                                             |     |
| ------------ | ------------ | --------------------------------------------------- | --- |
| UTILMD Strom | 1064         |                                                     |     |
| UTILMD Gas   | 345          |                                                     |     |
| REQOTE       | 264          | zusammen mit QUOTES, ORDERS, ORDRSP, ORDCHG         |     |
| QUOTES       | 264          | zusammen mit REQOTE, ORDERS, ORDRSP, ORDCHG         |     |
| ORDRSP       | 264          | zusammen mit REQOTE, QUOTES, ORDERS, ORDCHG         |     |
| ORDERS       | 264          | zusammen mit REQOTE, QUOTES, ORDRSP, ORDCHG         |     |
| ORDCHG       | 264          | zusammen mit REQOTE, QUOTES, ORDERS, ORDRSP         |     |
| MSCONS       | 164          |                                                     |     |
| UTILMD MaBis | 133          |                                                     |     |
| REMADV       | 91           | zusammen mit INVOIC                                 |     |
| INVOIC       | 91           | zusammen mit REMADV                                 |     |
| IFTSTA       | 82           |                                                     |     |
| CONTRL       | 72           | zusammen mit APERAK, ❌ enthält keine Prüfis         |     |
| APERAK       | 72           | zusammen mit CONTRL, ❌ enthält keine Prüfis         |     |
| PARTIN       | 69           |                                                     |     |
| UTILTS       | 34           |                                                     |     |
| ORDRSP       | 30           | zusammen mit ORDERS                                 |     |
| ORDERS       | 30           | zusammen mit ORDRSP                                 |     |
| PRICAT       | 25           |                                                     |     |
| COMDIS       | 10           | good test for tables which are above change history |     |
