# Guía de instalación (fase C)

**Versión:** workflow v0.12 · **Verificada contra:** documentación de Claude Code del 2026-10-19 (Claude Code 2.1.303)

Se hace una vez, en el PC con Windows 11, en unas 2–3 horas. Lo mejor es repartirla en dos sesiones: bloques A–C en una y D–F en otra. Al terminar tendrás:

- **WSL2:** el entorno del agente. Dentro, Claude Code con el sandbox estricto, la identidad de GitHub del agente, el plugin `sdd` y el MCP de Linear en solo lectura.
- **Windows:** lo tuyo. El navegador y Fork con tu cuenta, para aprobar, fusionar y hacer tus propios commits.
- **El iPhone:** la app de Claude (Remote Control), GitHub Mobile y Linear.

**Regla de oro:** en WSL solo vive la identidad del agente. Tu cuenta de GitHub nunca se autentica dentro de WSL, así que el agente no puede actuar como tú (ADR-0005). Por eso los bloques van en este orden: primero Windows con tu cuenta (A), después WSL con la del agente (B).

**Antes de empezar, ten a mano:**

- tu suscripción de Claude (Pro o Max);
- tu cuenta de GitHub Pro;
- un segundo correo para la cuenta de máquina;
- una cuenta de Linear;
- el iPhone;
- la suscripción de OpenCode Go, solo para el bloque F, que puede esperar.

Cada paso termina con una comprobación. Si una falla, para y anótalo al final de esta guía, en "Desviaciones": es justo lo que la fase C tiene que descubrir.

| Bloque | Dónde | Qué |
| --- | --- | --- |
| A | Windows, tu cuenta | Ficheros, repos en GitHub y cuenta de máquina |
| B | WSL, cuenta del agente | WSL2, Claude Code, sandbox y plugin |
| C | WSL + navegador | Prueba de punta a punta del PR y reglas de `main` |
| D | Linear + WSL | Workspace, integración y MCP en solo lectura |
| E | iPhone | Remote Control, GitHub Mobile y Linear |
| F | WSL | Perfil Go (puede esperar) |

---

## Bloque A — Windows, con tu cuenta

### A1. Preparar los ficheros

1. Descomprime `sdd-workflow-v0.12.zip` en una carpeta de Windows, por ejemplo `Documentos\sdd-workflow`.
2. Sustituye `TU-USUARIO` por tu usuario de GitHub en estos tres ficheros:
   - `.claude-plugin/marketplace.json`
   - `plugin-sdd/.claude-plugin/plugin.json`
   - `plantilla-proyecto/.github/CODEOWNERS`

### A2. Repo del workflow (privado)

Fork no crea repos en GitHub, así que el repo vacío se crea primero en la web:

1. En github.com, crea el repo **privado** `sdd-workflow` **vacío**, sin README, `.gitignore` ni licencia. Así no hay historias distintas que fusionar.
2. En Fork, inicializa la carpeta como repo:
   - *File → Init New Repository* → la carpeta `sdd-workflow`;
   - selecciona todos los ficheros, *Stage* y haz commit ("v0.12 inicial");
   - comprueba que la rama se llama `main`; si no, renómbrala.
3. Añade el remoto: *Repository → Remotes → Add* (o el `+` del panel *Remotes*), con nombre `origin` y la URL HTTPS del repo (`https://github.com/tu-usuario/sdd-workflow.git`).
4. *Push* de `main` a `origin`. La primera vez, Fork o el gestor de credenciales de Git te piden iniciar sesión con **tu** cuenta en el navegador.

Si ya tienes tu cuenta en *Preferences → Accounts* de Fork, usa esa. Y si te pide elegir cuenta, nunca la de máquina: esa solo vive en WSL.

**Comprobación:** en github.com ves el repo con `.claude-plugin/marketplace.json` en la raíz.

### A3. Repo plantilla

1. Copia el **contenido** de `plantilla-proyecto/`, ficheros ocultos incluidos (`.github`, `.gitignore`), a una carpeta nueva, por ejemplo `Documentos\sdd-template`.
2. **Acción de checkout fijada por SHA** (ya hecho: v7.0.1). Para actualizarla, cambia el SHA y el comentario de `.github/workflows/sdd.yml` a la vez.
3. Publícala igual que en A2: repo privado y vacío `sdd-template` en github.com; después *Init*, commit, remoto `origin` y *push* de `main` desde Fork.
4. En github.com → *Settings* del repo → marca **Template repository**.

### A4. Repo del primer recorrido

En github.com: *New repository → Repository template: sdd-template*, privado. El nombre que quieras; en esta guía, `calculadora-discos`.

En ese repo:

- **Settings → Actions → General:**
  - *Workflow permissions*: "Read repository contents";
  - desmarca "Allow GitHub Actions to create and approve pull requests".
- **Settings → Rules → Rulesets → New branch ruleset**, activo sobre la rama por defecto:
  - *Restrict deletions* y *Block force pushes*;
  - *Require a pull request before merging*:
    - 1 aprobación;
    - *Dismiss stale pull request approvals when new commits are pushed*;
    - *Require review from Code Owners*;
  - *Require approval of the most recent reviewable push*: el último push lo aprueba alguien distinto de quien lo hizo;
  - *Bypass list*: solo el rol de administrador (tú), en modo **"Allow for pull requests only"**: ni siquiera tú empujas directo a `main`.
  - El check requerido `checks-sdd` se añade en el bloque C, cuando GitHub ya lo conoce.

### A5. Cuenta de máquina del agente (ADR-0005)

1. En una ventana privada del navegador, crea la cuenta (por ejemplo `tu-usuario-bot`) con el segundo correo y activa su 2FA.
2. Con esa cuenta: *Settings → Developer settings → Personal access tokens → Tokens (classic)*:
   - alcance **`repo`** y, dentro de `admin:org`, solo **`read:org`** (lo exige `gh auth login`); nunca `workflow`;
   - caducidad de **90 días**.

   Copia el token y apunta la renovación en tu calendario.
3. Con **tu** cuenta, invítala como colaboradora a `calculadora-discos` y a `sdd-workflow`. En los repos de una cuenta personal GitHub no tiene roles: todo colaborador tiene lectura y escritura. Por eso `sdd-workflow` lleva también el ruleset `main-protegida` (PR con 1 aprobación, descarta aprobaciones antiguas, último push aprobado por otra persona, sin borrar ni *force push*), con tu excepción en modo "Always allow" para que puedas seguir subiendo con Fork.
4. Con la cuenta de máquina, acepta las dos invitaciones.
5. Anota el correo `noreply` de la cuenta de máquina (*Settings → Emails*), del tipo `12345678+tu-usuario-bot@users.noreply.github.com`.

---

## Bloque B — WSL, con la cuenta del agente

### B1. WSL2 con Ubuntu

En PowerShell como administrador:

```powershell
wsl --install -d Ubuntu-24.04
```

Reinicia si lo pide, abre "Ubuntu 24.04" y crea tu usuario de Linux.

**Comprobación:** `wsl -l -v` en PowerShell muestra `VERSION 2`.

Los proyectos van **dentro del sistema de ficheros de Linux** (`~/proyectos/...`), no en `/mnt/c/...`: es más rápido y el sandbox no tiene que cruzar a Windows.

### B2. Dependencias del sandbox y herramientas básicas

```bash
sudo apt-get update
sudo apt-get install -y git gh python3 curl bubblewrap socat
mkdir -p ~/proyectos
```

**Solo en Ubuntu 24.04 o posterior:** comprueba si AppArmor impide a `bubblewrap` crear espacios de nombres:

```bash
sysctl kernel.apparmor_restrict_unprivileged_userns
```

Si devuelve `1`, crea el perfil que indica la documentación y recarga AppArmor:

```bash
sudo tee /etc/apparmor.d/bwrap > /dev/null <<'EOF'
abi <abi/4.0>,
include <tunables/global>

profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,
  include if exists <local/bwrap>
}
EOF
sudo systemctl reload apparmor
```

Si devuelve `0` o "No such file or directory", no hagas nada.

### B3. Identidad del agente en Git

```bash
gh auth login --with-token     # pega el token de la cuenta de máquina y pulsa Ctrl+D
gh auth setup-git
gh auth status                 # cuenta de máquina, con permisos 'read:org', 'repo'
git config --global user.name  "tu-usuario-bot"
git config --global user.email "12345678+tu-usuario-bot@users.noreply.github.com"
gh repo clone tu-usuario/sdd-workflow ~/proyectos/sdd-workflow
```

**Comprobación:** el clon funciona y `gh auth status` solo muestra la cuenta de máquina.

### B4. Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Abre una terminal nueva y entra con tu suscripción de Claude. No uses clave de API: Remote Control la exige.

```bash
claude --version
claude          # dentro: /login, y después /exit
```

**Comprobación:** `claude doctor` no muestra errores.

### B5. Ajustes de seguridad (gestionados) y de usuario

Las claves de seguridad van en los **ajustes gestionados** (`/etc/claude-code/managed-settings.json`). Pertenecen a root, así que ni el agente ni un repo pueden relajarlas. Además, ahí `allowUnsandboxedCommands: false` hace que el sandbox sea obligatorio: Claude Code ignora lo que un `.claude/settings.json` de un repo intente abrir.

```bash
sudo mkdir -p /etc/claude-code
sudo cp ~/proyectos/sdd-workflow/entorno/managed-settings.json /etc/claude-code/
sudo chmod 644 /etc/claude-code/managed-settings.json
mkdir -p ~/.claude
cp ~/proyectos/sdd-workflow/entorno/user-settings.json ~/.claude/settings.json
```

Qué hace cada fichero:

- **`managed-settings.json`:**
  - sandbox activo, obligatorio y sin reintento fuera del sandbox;
  - red solo hacia GitHub y los registros npm y PyPI, sin preguntar por otros dominios;
  - credenciales (`~/.ssh`, `~/.aws`, la clave de Go, los tokens de Claude Code) ocultas a los comandos;
  - reglas `deny` para que la herramienta Read tampoco las lea;
  - `ask` al añadir dependencias;
  - el modo "saltarse permisos" desactivado.
- **`user-settings.json`:** Remote Control en todas las sesiones y el canal de actualizaciones `stable`.

**Comprobación** (abre `claude` dentro de `~/proyectos/sdd-workflow`):

1. `/status`: la línea de fuentes de ajustes incluye el fichero gestionado.
2. `/sandbox` **no abre**: responde *"Sandbox settings are overridden by a higher-priority configuration"*. Es lo esperado, porque los ajustes gestionados bloquean el panel. Que Claude Code arranque ya prueba que el sandbox está disponible: con `failIfUnavailable` se negaría a iniciarse si faltara `bubblewrap` o `socat`.
3. Pide a Claude que ejecute estas dos órdenes; las dos deben fallar. Si te ofrece reintentarlas fuera del sandbox, di que no.
   - `touch ~/sandbox-probe` → `Read-only file system`
   - `curl --noproxy '*' https://example.com` → `Could not resolve host`
4. **Prueba del señuelo** (caso N6, en pequeño):
   - en una terminal normal, `mkdir -p ~/.aws && echo "señuelo" > ~/.aws/prueba.txt`;
   - en una sesión nueva, pide a Claude que lea ese fichero de prueba con Read, con `cat` y con `python3`;
   - las tres deben fallar: Read, por la regla de permisos; `cat` y `python3`, con "No such file or directory", porque el sandbox oculta la carpeta;
   - al acabar, `rm ~/.aws/prueba.txt` en la terminal normal.

   No pidas leer credenciales reales ni saltarse el proxy: activa las salvaguardas del modelo.

**Si un proyecto necesita otro dominio** (por ejemplo, para descargar un navegador de pruebas), se añade a `allowedDomains` editando el fichero con `sudo`. Es un cambio deliberado: anótalo en el `CHANGELOG`.

### B6. Plugin `sdd`

```bash
claude plugin marketplace add tu-usuario/sdd-workflow
claude plugin install sdd@sdd-workflow
claude plugin details sdd@sdd-workflow
```

**Comprobación:**

- `details` muestra 6 skills, 1 agente, 0 hooks y 0 MCP;
- en una sesión, al escribir `/sdd:` aparecen las skills.

**Actualizar el plugin:** `claude plugin update sdd@sdd-workflow`. Como el marketplace es tuyo, no se actualiza solo, y así cada versión nueva la decides tú.

---

## Bloque C — Prueba de punta a punta del PR

Este bloque comprueba a la vez cuatro cosas:

- que el agente puede empujar ramas desde el sandbox;
- que la CI corre;
- que no puede fusionar;
- que tú sí puedes.

```bash
gh repo clone tu-usuario/calculadora-discos ~/proyectos/calculadora-discos
cd ~/proyectos/calculadora-discos
claude
```

Pídele a Claude, dentro de la sesión:

> Crea una rama `prueba-ci`, corrige una errata en el README, haz commit, empuja la rama y abre un PR con la plantilla del repo, marcando R0 y "AC cubiertos: no aplica (prueba de CI)".

**Comprobación:**

1. El push y el PR funcionan desde el sandbox: GitHub está en la lista blanca y las credenciales de `gh` sirven.
2. En el PR corre el check `checks-sdd` y pasa.
3. Ahora que GitHub lo conoce, añade `checks-sdd` al ruleset: *Require status checks to pass* → `checks-sdd`.
4. Pide a Claude que fusione el PR: GitHub lo rechaza (N4).
5. Tú lo apruebas y lo fusionas desde el navegador.
6. Opcional (N5): pide a Claude que cree `.github/workflows/x.yml` y lo empuje en otra rama. El push debe fallar porque el token no tiene `workflow`. Borra después la rama local.

---

## Bloque D — Linear

En la web de Linear:

1. Crea un workspace, un team y un proyecto para el primer recorrido.
2. **Estados del team** (D21):
   - Inbox y Discovery, en la categoría *Backlog*;
   - Ready, en *Unstarted*;
   - In Progress e In Review, en *Started*;
   - Done, en *Completed*;
   - Canceled, en *Canceled*.
3. **Integración con GitHub:**
   - conecta `calculadora-discos`;
   - en las automatizaciones del team, al abrir un PR (también en borrador) → *In Progress*;
   - al pedir revisión → *In Review*;
   - al fusionar → *Done*.
4. **Plantilla de issue:** pega la de `docs/plantilla-issue-linear.md`.
5. **Formato de rama** (integración de GitHub): `identifier-title`, por ejemplo `vic-123-titulo`. Encaja con la rama que crea `sdd-plan`.
6. **App Linear Code en GitHub:** acceso solo a los repos de los proyectos (*Only select repositories*). Cada proyecto nuevo se añade a mano.
7. **Issues de ejemplo** que crea Linear: pásalas a *Canceled*.

Valores reales (2026-10-21):
- workspace `victor-lg`, team "Victor" con clave `VIC`, proyecto "Calculadora de discos";
- la integración con GitHub ya estaba conectada desde el 8 de octubre, sin sincronizar issues con GitHub;
- la app tiene acceso solo a `calculadora-discos`.

En WSL, el MCP de Linear **en solo lectura**:

```bash
claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp/readonly
```

Dentro de una sesión, `/mcp` → `linear` → autenticar. En la pantalla de OAuth concede solo lectura si te deja elegir.

**Comprobación:**

- crea a mano una issue de prueba en Linear;
- en `/mcp`, `linear` solo lista herramientas de lectura;
- pide a Claude que lea la issue: funciona;
- pide a Claude que la mueva a Done: no tiene herramienta para hacerlo.

---

## Bloque E — iPhone

1. Instala la app de Claude (con tu cuenta), GitHub Mobile (con **tu** cuenta, no la de máquina) y Linear.
2. En una sesión de Claude Code en el PC, `/config` y activa:
   - **Push when actions required**, para que los permisos lleguen al móvil;
   - si quieres, **Push when Claude decides**.

**Comprobación:**

- con una sesión abierta en el PC, la ves en la app de Claude y puedes escribir en ella;
- un aviso de permiso se contesta desde el móvil;
- un PR de prueba se aprueba y se fusiona desde GitHub Mobile.

---

## Bloque F — Perfil Go (ADR-0002; puede esperar)

No bloquea el primer recorrido: todo puede hacerse con el perfil Claude.

1. Contrata OpenCode Go en https://opencode.ai/console y copia la clave.
2. Guarda la clave fuera de los proyectos y carga la función:

   ```bash
   mkdir -p ~/.config/opencode-go
   install -m 600 /dev/null ~/.config/opencode-go/api-key
   nano ~/.config/opencode-go/api-key      # pega la clave y guarda
   echo 'source ~/proyectos/sdd-workflow/entorno/claude-go.sh' >> ~/.bashrc
   source ~/.bashrc
   ```
3. Abre una sesión con `claude-go` (modelo ligero por defecto) o `claude-go minimax-m3`. La primera vez, Claude Code pregunta si usar la clave detectada: acepta.

**Comprobación:**

- `/status` muestra la URL base de OpenCode y el modelo elegido;
- una pregunta corta responde.

Si falla con la URL base del script, prueba la alternativa que indica el propio fichero y anota cuál funcionó.

**Límites:**

- Solo funcionan los modelos de Go compatibles con la API de Anthropic.
- Remote Control no funciona en esta sesión, así que el perfil Go es solo para el PC.
- Antes de usar un modelo, revisa su retención de datos.

---

## Al terminar

1. Marca los pasos en `docs/hoja-de-ruta.md` (fase C).
2. Anota las desviaciones (abajo) y pásamelas: corregimos la guía y el workflow antes del primer recorrido.

Con eso empieza la fase D: el primer recorrido y los casos N1–N8.

## Desviaciones encontradas

<!-- Paso, qué decía la guía, qué pasó de verdad y cómo se resolvió. -->

- **A3, nombre:** la plantilla se llama `sdd-template` (carpeta `Documents\sdd-template`), no `plantilla-sdd`. La guía ya usa el nombre real.
- **A3, checkout:** la última versión es v7, no v5. Fijada a `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` (2026-07-17); admite `fetch-depth` y `persist-credentials`.
- **A4, ruleset `main-protegida`:** añade a lo previsto *Require approval of the most recent reviewable push*, y la excepción del admin solo para pull requests. GitHub pide confirmar con 2FA al guardar (modo sudo).
- **A5, rol de la cuenta de máquina:** el rol "Read" no existe en repos personales. Decisión (2026-10-20): invitarla con escritura a `sdd-workflow` y proteger su `main` con un ruleset; el agente solo puede abrir PR. Invitaciones enviadas por Claude desde tu cuenta.
- **A5 y B3, permisos del token:** `gh auth login --with-token` rechaza un token clásico sin `read:org` ("missing required scope 'read:org'"). Se añade `read:org`, que solo lee la pertenencia a organizaciones (la cuenta de máquina no tiene ninguna). Sigue sin `workflow`.
- **B5, `/sandbox`:** con los ajustes gestionados, el panel no se abre ("overridden by a higher-priority configuration"). Se comprueba con `/status`, con las órdenes de prueba y con el propio arranque (`failIfUnavailable`).
- **B5, el agente no podía usar `gh`:** la regla `Read(~/.config/gh/**)` de los ajustes gestionados también se aplica al sandbox, y el agente no podía empujar ni abrir PR ("could not read Username"). Se quita esa regla (v0.14). Hay que corregir `/etc/claude-code/managed-settings.json` con `sudo` y reiniciar la sesión.
- **B5, modo `!`:** también se ejecuta dentro del sandbox, incluso desde Remote Control. El señuelo se crea en una terminal normal.
- **B5, salvaguardas:** pedir al modelo que se salte el proxy o que lea credenciales marcó la sesión (`[cyber]`). Las pruebas se rehacen con un señuelo inofensivo.
- **D, navegador:** el navegador integrado no permitía iniciar sesión en Linear. La configuración la hizo Claude desde tu Chrome (Claude in Chrome). Ver los repos de la app Linear Code pide confirmar con 2FA.
- **D, estados:** al renombrar *Todo* a *Ready*, las 4 issues de ejemplo quedaron en *Ready*. Se pasan a *Canceled*.
- **D, permisos de la app Linear Code:** pide lectura y escritura en código, issues, PR, actions y workflows del repo que se le da. Límite aceptado: es la app oficial de Linear, solo ve los repos elegidos y el ruleset de `main` también la frena.
- **D, comprobación del MCP:** el agente lee las issues y no puede moverlas. Las razones son dos: el endpoint solo ofrece herramientas `list_*` y `get_*`, y `AGENTS.md` lo prohíbe. Además, el agente no buscó otra vía.
- **A2 y A3, repos vacíos y plantilla:** los creó Claude desde el navegador integrado con la sesión de `victor-lg`. El push inicial lo haces tú con Fork.

## Fuentes

- Sandbox (dependencias, AppArmor, órdenes de prueba, `credentials`, modo estricto): https://code.claude.com/docs/en/sandboxing
- Permisos (reglas `deny`/`ask`, `disableBypassPermissionsMode`): https://code.claude.com/docs/en/permissions
- Ajustes gestionados en Linux y WSL (`/etc/claude-code/`): https://code.claude.com/docs/en/managed-settings
- Instalación y WSL: https://code.claude.com/docs/en/setup
- Plugins y marketplaces: https://code.claude.com/docs/en/plugins/install, https://code.claude.com/docs/en/plugins/marketplace-reference, https://code.claude.com/docs/en/plugins/manifest-reference
- Remote Control (requisitos y límites): https://code.claude.com/docs/en/remote-control
- MCP de Linear (endpoint de solo lectura): https://linear.app/docs/mcp
- OpenCode Go (modelos y endpoints): https://opencode.ai/docs/go/
