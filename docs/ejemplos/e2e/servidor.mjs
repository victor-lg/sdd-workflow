// Sirve app/ en http://127.0.0.1:4173 para los E2E del ejemplo, sin dependencias.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(fileURLToPath(new URL(".", import.meta.url)), "app");
const TIPOS = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript" };

createServer(async (peticion, respuesta) => {
  const ruta = new URL(peticion.url, "http://localhost").pathname;
  const fichero = normalize(join(RAIZ, ruta === "/" ? "index.html" : ruta));
  if (!fichero.startsWith(RAIZ + sep)) {
    respuesta.writeHead(403).end();
    return;
  }
  try {
    const cuerpo = await readFile(fichero);
    respuesta.writeHead(200, { "content-type": TIPOS[extname(fichero)] ?? "application/octet-stream" }).end(cuerpo);
  } catch {
    respuesta.writeHead(404).end();
  }
}).listen(4173, "127.0.0.1");
