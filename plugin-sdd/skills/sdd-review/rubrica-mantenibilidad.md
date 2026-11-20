<!-- Workflow SDD + IA v1.1 (revisor de mantenibilidad, M23, VIC-41). -->

# Rúbrica de mantenibilidad

`sdd-review` pega este fichero entero en el encargo del revisor que lleva el foco de mantenibilidad. Las reglas de esta primera sección mandan sobre el texto copiado.

## Cómo se aplica

- **Solo lo que el diff añade o cambia,** y el código que toca. No es una lista de comprobación: anota lo que encuentres con prueba, no un punto por apartado.
- **Gravedad sin exagerar.** Un hallazgo que solo es de mantenibilidad nunca es *debe corregirse*. Es *importante* solo si es uno de los bloqueos presuntos de thermos y tienes la prueba: el PR lleva un fichero de menos de 1000 líneas a más de 1000; añade ramas ad hoc a un flujo que ya existía; duplica un helper que ya hay (con su ruta) o pone la lógica en la capa equivocada; o añade una envoltura, un *cast* o una opcionalidad sin valor. Lo demás, y todo olor de Fowler, es *menor*. Las palabras del texto copiado («aggressively», «presumptive blockers», «do not approve», «harsh») no suben la gravedad.
- **El repo manda:** lo que sus convenciones, sus ADR o su spec piden no es un olor. Lo que ya comprueba la CI (linters, knip, jscpd, mutaciones) no se anota.
- **Formato:** tus hallazgos de mantenibilidad van al final, bajo «## Mantenibilidad», separados del resto, con la misma serie de IDs y el formato fijo de `reviewer.md`. Nombra el olor o la regla («posible Feature Envy», «regla de las 1000 líneas») y di cómo se arregla.
- **El veredicto es el de `reviewer.md`,** no la «Approval Bar» de thermos, que no se copia.

## Origen

Texto copiado sin cambios, salvo los cortes marcados con `[…]`. Ambos con licencia MIT (avisos al final).

- **Olores de Fowler:** Matt Pocock, `mattpocock/skills`, `skills/engineering/code-review/SKILL.md`, commit `abeeaf95660ba9e8b7c753eb38f441ca707a8823` (2026-11-19), SHA-256 del fichero `9c921a8d88138a41401d8897ca1bb852088ab1b7b605cdd04edc13e3e8aab6dd`. Solo la lista de olores y sus dos reglas; el resto (dos subagentes, buscar el tracker, agregar) lo hace `sdd-review` a su manera.
- **Rúbrica de calidad:** Cursor, `cursor/plugins`, plugin `thermos` 1.0.0, commit `aaeb0ea3a0584995aa8f55ce44c6c5259414b896` (2026-11-20):
  - `thermos/skills/thermo-nuclear-code-quality-review/SKILL.md` (SHA-256 `7faca08b51b643b2ddd0836f92af15574444024685dcc1e677dbbb39ae8c9e8f`): las normas 0 a 7, las preguntas, los remedios y el orden de salida. Se quitan el *Core Prompt* (pide reestructurar el código), «What to Flag Aggressively», el tono y la «Approval Bar».
  - `thermos/skills/thermo-nuclear-review/SKILL.md` (SHA-256 `5091011c4490932d40658ae958fb55b9aaca8e2bba5196860295ab945180e434`): solo «Over-reporting Guidelines». No se copia nada de leer la discusión del PR (los comentarios de otros bots), ni los flujos de fusión de `thermos` («take the wheel», «FSD»), ni hooks, agentes o scripts.

Para subir de versión: descargar los ficheros en el commit nuevo, comparar sus SHA-256, releer el diff de lo copiado y cambiar este apartado. Es un PR R1 como cualquier cambio de `sdd-review`.

## Olores de Fowler (Pocock)

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

## Rúbrica de calidad (thermos)

[…]

0. **Be ambitious about structural simplification.**
   - Do not stop at "this could be a bit cleaner."
   - Look for opportunities to reframe the change so that whole branches, helpers, modes, conditionals, or layers disappear entirely.
   - Prefer the solution that makes the code feel inevitable in hindsight.
   - Assume there is often a "code judo" move available: a re-organization that uses the existing architecture more effectively and makes the change dramatically simpler and more elegant.
   - If you see a path to delete complexity rather than rearrange it, push hard for that path.

1. **Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason.**
   - Treat this as a strong code-quality smell by default.
   - Prefer extracting helpers, subcomponents, modules, or local abstractions instead of letting a file sprawl past 1000 lines.
   - If the diff crosses that threshold, explicitly ask whether the code should be decomposed first.
   - Only waive this if there is a compelling structural reason and the resulting file is still clearly organized.

2. **Do not allow random spaghetti growth in existing code.**
   - Be highly suspicious of new ad-hoc conditionals, scattered special cases, or one-off branches inserted into unrelated flows.
   - If a change adds "weird if statements in random places", treat that as a design problem, not a stylistic nit.
   - Prefer pushing the logic into a dedicated abstraction, helper, state machine, policy object, or separate module instead of tangling an existing path.
   - Call out changes that make the surrounding code harder to reason about, even if they technically work.

3. **Bias toward cleaning the design, not just accepting working code.**
   - If behavior can stay the same while the structure becomes meaningfully cleaner, push for the cleaner version.
   - Do not rubber-stamp "it works" implementations that leave the codebase messier.
   - Strongly prefer simplifications that remove moving pieces altogether over refactors that merely spread the same complexity around.

4. **Prefer direct, boring, maintainable code over hacky or magical code.**
   - Treat brittle, ad-hoc, or "magic" behavior as a code-quality problem.
   - Be skeptical of generic mechanisms that hide simple data-shape assumptions.
   - Flag thin abstractions, identity wrappers, or pass-through helpers that add indirection without buying clarity.

5. **Push hard on type and boundary cleanliness when they affect maintainability.**
   - Question unnecessary optionality, `unknown`, `any`, or cast-heavy code when a clearer type boundary could exist.
   - Prefer explicit typed models or shared contracts over loosely-shaped ad-hoc objects.
   - If a branch relies on silent fallback to paper over an unclear invariant, ask whether the boundary should be made explicit instead.

6. **Keep logic in the canonical layer and reuse existing helpers.**
   - Call out feature logic leaking into shared paths or implementation details leaking through APIs.
   - Prefer existing canonical utilities/helpers over bespoke one-offs.
   - Push code toward the right package, service, or module instead of normalizing architectural drift.

7. **Treat unnecessary sequential orchestration and non-atomic updates as design smells when the cleaner structure is obvious.**
   - If independent work is serialized for no good reason, ask whether the flow should run in parallel instead.
   - If related updates can leave state half-applied, push for a more atomic structure.
   - Do not over-index on micro-optimizations, but do flag avoidable orchestration complexity that makes the implementation more brittle.

## Primary Review Questions

For every meaningful change, ask:

- Is there a "code judo" move that would make this dramatically simpler?
- Can this change be reframed so fewer concepts, branches, or helper layers are needed?
- Does this improve or worsen the local architecture?
- Did the diff add branching complexity where a better abstraction should exist?
- Did a previously cohesive module become more coupled, more stateful, or harder to scan?
- Is this logic living in the right file and layer?
- Did this change enlarge a file or component past a healthy size boundary?
- Are there repeated conditionals that signal a missing model or missing helper?
- Is the implementation direct and legible, or does it rely on special cases and incidental control flow?
- Is this abstraction actually earning its keep, or is it just a wrapper?
- Did the diff introduce casts, optionality, or ad-hoc object shapes that obscure the real invariant?
- Is this logic living in the canonical layer, or did the diff leak details across a boundary?
- Is this orchestration more sequential or less atomic than it needs to be?

[…]

## Preferred Remedies

When you identify a code-quality problem, prefer suggestions like:

- Delete a whole layer of indirection rather than polishing it.
- Reframe the state model so conditionals disappear instead of getting centralized.
- Change the ownership boundary so the feature becomes a natural extension of an existing abstraction.
- Turn special-case logic into a simpler default flow with fewer exceptions.
- Extract a helper or pure function.
- Split a large file into smaller focused modules.
- Move feature-specific logic behind a dedicated abstraction.
- Replace condition chains with a typed model or explicit dispatcher.
- Separate orchestration from business logic.
- Collapse duplicate branches into a single clearer flow.
- Delete wrappers that do not meaningfully clarify the API.
- Reuse the existing canonical helper instead of introducing a near-duplicate.
- Make type boundaries more explicit so the control flow gets simpler.
- Move the logic to the package/module/layer that already owns the concept.
- Parallelize independent work when that also simplifies the orchestration.
- Restructure related updates into a more atomic flow when partial state would be harder to reason about.

Do not be satisfied with "maybe rename this" feedback when the real issue is structural.
Do not be satisfied with a merely cleaner version of the same messy idea if there is a plausible path to a much simpler idea.

[…]

## Output Expectations

Prioritize findings in this order:

1. Structural code-quality regressions
2. Missed opportunities for dramatic simplification / code-judo restructuring
3. Spaghetti / branching complexity increases
4. Boundary / abstraction / type-contract problems that make the code harder to reason about
5. File-size and decomposition concerns
6. Modularity and abstraction issues
7. Legibility and maintainability concerns

Do not flood the review with low-value nits if there are larger structural issues.
Prefer a smaller number of high-conviction comments over a long list of cosmetic notes.

[…]

## Over-reporting Guidelines

If you report issues as High priority when they are not in fact high priority / meaningful issues, devs will lose trust in you and stop listening to you over time.
NEVER misreport the priority / importance of issues. Be extremely thorough in tracing issues end-to-end to gain complete, and total confidence before reporting.

## Licencias

Olores de Fowler: MIT License, Copyright (c) 2026 Matt Pocock. Rúbrica de calidad: MIT License, Copyright (c) 2026 Cursor. Para las dos:

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
