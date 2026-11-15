import { test } from "node:test";
import assert from "node:assert/strict";
import { tbAGb } from "../src/unidades.js";

test("1 TB son 1024 GB", () => assert.equal(tbAGb(1), 1024));
test("0 TB son 0 GB", () => assert.equal(tbAGb(0), 0));
test("un tamaño negativo se rechaza", () => assert.throws(() => tbAGb(-1), RangeError));
