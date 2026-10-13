# Engine keys and paper labels

Exact keys in the delivered output are:

| Engine key | Description |
|---|---|
| `QQQ` | Nasdaq-100 buy and hold |
| `SPY` | S&P 500 buy and hold |
| `Static_70_20_10` | See the exact branch in engine.py and the generated tables; retained legacy key |
| `Static_50_20_20_10` | See the exact branch in engine.py and the generated tables; retained legacy key |
| `Vol15` | See the exact branch in engine.py and the generated tables; retained legacy key |
| `RegimeRule` | R: transparent state rule |
| `BoydSimple` | M: simple constrained optimizer |
| `BoydRidge` | MR: ridge optimizer |
| `RegimeRobust` | RM: state-dependent robust optimizer |
| `ProbabilityRobust` | See the exact branch in engine.py and the generated tables; retained legacy key |
| `MacroRidge_Exploratory` | See the exact branch in engine.py and the generated tables; retained legacy key |

Keys are retained for numerical continuity. In particular, `BoydSimple` denotes the independently implemented monthly extension called M in the paper; it is not authorship attribution, an endorsement or an exact replica of the reference authors' code.
