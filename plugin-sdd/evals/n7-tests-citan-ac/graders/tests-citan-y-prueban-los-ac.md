---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Un test por AC: cita SPEC-DISCO-003/AC-NN junto al def test y, dentro de ese test, compara la salida del AC
# (en cualquier orden, o a través de una variable intermedia).
# Límite conocido: un test con @pytest.mark.parametrize no casa.
pattern: '^(?=[\s\S]*(#[^\n]*SPEC-DISCO-003/AC-01[^\n]*\n([ \t]*@[^\n]*\n)*[ \t]*def test\w*\(|def test\w*\([^\n]*SPEC-DISCO-003/AC-01|def test\w*\([^\n]*\n[ \t]+[^\n]*SPEC-DISCO-003/AC-01)((?!\n\s*def )[\s\S]){0,400}?(gb_a_tb\(\s*1024\s*\)\s*==\s*(pytest\.approx\(\s*)?1(\.0)?\b|\b(pytest\.approx\(\s*)?1(\.0)?\)?\s*==\s*gb_a_tb\(\s*1024\s*\)|(?<r1>\w+)\s*=\s*gb_a_tb\(\s*1024\s*\)((?!\n\s*def )[\s\S]){0,200}?(\b\k<r1>\s*==\s*(pytest\.approx\(\s*)?1(\.0)?\b|\b(pytest\.approx\(\s*)?1(\.0)?\)?\s*==\s*\k<r1>\b)))(?=[\s\S]*(#[^\n]*SPEC-DISCO-003/AC-02[^\n]*\n([ \t]*@[^\n]*\n)*[ \t]*def test\w*\(|def test\w*\([^\n]*SPEC-DISCO-003/AC-02|def test\w*\([^\n]*\n[ \t]+[^\n]*SPEC-DISCO-003/AC-02)((?!\n\s*def )[\s\S]){0,400}?(tb_a_gb\(\s*0?\.5\s*\)\s*==\s*(pytest\.approx\(\s*)?512(\.0)?\b|\b(pytest\.approx\(\s*)?512(\.0)?\)?\s*==\s*tb_a_gb\(\s*0?\.5\s*\)|(?<r2>\w+)\s*=\s*tb_a_gb\(\s*0?\.5\s*\)((?!\n\s*def )[\s\S]){0,200}?(\b\k<r2>\s*==\s*(pytest\.approx\(\s*)?512(\.0)?\b|\b(pytest\.approx\(\s*)?512(\.0)?\)?\s*==\s*\k<r2>\b)))'
weight: 4
---
