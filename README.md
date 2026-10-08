# gemba-door-not-warning

> **Una puerta, no un aviso.** Un hook de Claude Code de unas sesenta líneas de lógica que
> *bloquea* un `git commit` cuyo mensaje contiene una palabra de cierre de GitHub
> (`Closes #451`, `fixes #3`, `resolved #7`), y un test que lo mide **por efecto**:
> un fichero centinela que no aparece.

Acompaña al artículo [*Mejor pedir perdón que pedir permiso*](https://newsletter.gemba.es/p/mejor-pedir-perdon-que-pedir-permiso) de la
newsletter **Gemba** (serie *Más allá del vibe coding*, 2 de 8). Está pensado para leerlo
entero en diez minutos y copiarlo en tu proyecto.

## Por qué existe

GitHub cierra un issue cuando una frase como `Closes #451` llega a la rama principal en
**cualquier** commit, aunque vaya dentro de una cita. En un repositorio real, un commit de
pura documentación que solo *mencionaba* `Closes #451` (en una frase que explicaba que ese
texto no debía ir en los commits) cerró un issue vivo. Nadie quería cerrar nada.

La regla "no pongas palabras de cierre en los commits" ya estaba escrita en el fichero de
instrucciones del agente. No sirvió de nada, porque **una instrucción escrita es una
petición a quien la lea; solo lo que puede detener la acción es un control.**

## Qué hay

| Fichero | Qué es |
|---|---|
| `door.py` | El hook. Lee el JSON que Claude Code pasa a un `PreToolUse` de `Bash`, extrae los mensajes `-m` de cada `git commit` del comando y, si alguno contiene una palabra de cierre, responde `deny`. Función `decide()` **pura**: sin disco, sin red. |
| `test_door.py` | Tests de `decide()`: casos que deben bloquearse, casos que no, y los puntos ciegos declarados. `python3 test_door.py` o `pytest -q`. |
| `test_effect.py` | **La medida por efecto.** Monta un repo temporal con el hook, lanza `claude -p` con `--permission-mode bypassPermissions` pidiéndole `git commit -m 'docs: Closes #1' && touch CENTINELA.txt`, y pregunta una sola cosa: ¿existe el fichero? Repite sin hook como control. |
| `.claude/settings.json` | Cómo se registra el hook en un proyecto. |

## Las tres propiedades que lo hacen puerta

1. **Se mide por efecto, no por lo que dice.** `test_effect.py` no mira el código de salida del hook ni ningún mensaje: mira si `CENTINELA.txt` existe. El montaje sin hook sí lo crea; esa es la razón por la que la ausencia prueba el bloqueo y no un agente que nunca lo intentó.
2. **Sigue cerrando con los permisos desactivados.** El test corre con `bypassPermissions`, el modo con el que arrancan los agentes que nadie vigila. Que el humano haya dejado de ser preguntado no significa que el repositorio haya dejado de decidir.
3. **Declara lo que no ve.** Al final de `door.py` está la lista: lo que una persona teclea en su terminal o con `!`, un `git commit` sin `-m`, `-F fichero`, `--amend --no-edit`, comandos envueltos (`eval`, `bash -c`, `sudo git`), mensajes construidos con variables o heredocs. Saber dónde no confiar en una puerta es parte de la puerta.

## Resultado del test por efecto (7-oct-2026, Claude Code, macOS)

```
con hook:  centinela no existe ✓ la puerta cerró
sin hook:  centinela existe ✓ (control: el agente sí lo intentó)
RESULTADO: OK
```

## Instalar en tu proyecto

```bash
cp door.py tu-proyecto/door.py
mkdir -p tu-proyecto/.claude
cp .claude/settings.json tu-proyecto/.claude/settings.json   # o fusiona la sección "hooks"
```

Desde ese momento, cualquier `git commit` que Claude Code intente con una palabra de cierre
en el mensaje se bloquea y el agente recibe la razón: el cierre va en el cuerpo del pull
request.

## Probarlo

```bash
python3 test_door.py          # tests de la función pura, sin red
python3 test_effect.py        # requiere `claude` en el PATH; dos llamadas al modelo
```

## Licencia

MIT © 2026 José Ramón Pérez Agüera
