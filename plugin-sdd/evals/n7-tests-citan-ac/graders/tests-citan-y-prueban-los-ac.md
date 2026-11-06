---
type: regex
# Crítico: un test por AC que cita SPEC-DISCO-003/AC-NN y llama a la función con la entrada del AC.
pattern: '^(?=[\s\S]*(#[^\n]*SPEC-DISCO-003/AC-01[^\n]*\n([ \t]*@[^\n]*\n)*[ \t]*def test\w*\(|def test\w*\([^\n]*SPEC-DISCO-003/AC-01|def test\w*\([^\n]*\n[ \t]+[^\n]*SPEC-DISCO-003/AC-01)[\s\S]{0,400}?gb_a_tb\(\s*1024\s*\))(?=[\s\S]*(#[^\n]*SPEC-DISCO-003/AC-02[^\n]*\n([ \t]*@[^\n]*\n)*[ \t]*def test\w*\(|def test\w*\([^\n]*SPEC-DISCO-003/AC-02|def test\w*\([^\n]*\n[ \t]+[^\n]*SPEC-DISCO-003/AC-02)[\s\S]{0,400}?tb_a_gb\(\s*0?\.5\s*\))'
weight: 4
---
