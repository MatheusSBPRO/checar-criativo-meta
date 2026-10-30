#!/usr/bin/env python3
"""Peneira de política de publicidade da Meta: roda ANTES de subir o criativo.

Lê tudo o que vai para o anúncio (fala do vídeo, texto da imagem, copy, título e página de destino)
e marca os trechos que costumam dar reprovação ou bloqueio. Ela só filtra; quem decide é você,
ou o Claude/Codex, que leem o trecho no contexto (veja .claude/skills/checar-criativo/SKILL.md).

Uso:
  python3 scripts/checar_criativo.py criativos/                    # pasta inteira
  python3 scripts/checar_criativo.py AD01.mp4 AD02.png --copy copy.txt --url https://sua.pagina
  python3 scripts/checar_criativo.py --texto "Ganhe R$ 300 por dia jogando"

O que ele faz com cada arquivo:
  vídeo/áudio  usa a transcrição <nome>.txt ao lado do arquivo; se não houver, transcreve com o
               whisper local (mlx-whisper ou openai-whisper) e salva em <pasta>/.transcricoes/
  imagem       usa <nome>.txt ao lado da imagem (o texto escrito na arte). Sem ele, fica PENDENTE:
               peça ao Claude/Codex para ler a imagem e gravar esse .txt
  .txt / .md   lê direto

Saída: um veredito por item.
  FORA     tem trecho de risco alto: não sobe sem reescrever
  REVISAR  tem trecho que depende do contexto: leia antes de subir
  LIMPO    nada no filtro (não é garantia de aprovação)
  PENDENTE sem texto para checar
Código de saída: 2 se houver FORA, 1 se houver REVISAR ou PENDENTE, 0 se tudo LIMPO.
Só biblioteca padrão do Python 3.9+.
"""
import argparse
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TERMOS = RAIZ / "referencias" / "termos.json"

VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".aac"}
IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"}
TEXTO = {".txt", ".md"}
PESO = {"ALTO": 3, "MEDIO": 2, "BAIXO": 1}


def normalizar(t):
    """minúsculo e sem acento, para o padrão casar com 'eleição', 'ELEICAO' e 'eleicao'."""
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def carregar_regras(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    regras = []
    for cat in dados["categorias"]:
        for p in cat["padroes"]:
            regras.append((cat, re.compile(p)))
    return regras


def checar(texto, regras):
    """Devolve a lista de achados: categoria, severidade e o trecho com um pouco de contexto."""
    norm = normalizar(texto)
    achados, vistos = [], set()
    for cat, rx in regras:
        for m in rx.finditer(norm):
            chave = (cat["id"], m.start())
            if chave in vistos:
                continue
            vistos.add(chave)
            ini, fim = max(0, m.start() - 45), min(len(norm), m.end() + 45)
            trecho = norm[ini:fim].replace("\n", " ").strip()
            achados.append({
                "categoria": cat["id"],
                "nome": cat["nome"],
                "severidade": cat["severidade"],
                "achou": m.group(0),
                "trecho": f"...{trecho}...",
            })
    achados.sort(key=lambda a: -PESO[a["severidade"]])
    return achados


def veredito(achados):
    if not achados:
        return "LIMPO"
    if any(a["severidade"] == "ALTO" for a in achados):
        return "FORA"
    return "REVISAR"


def motor_whisper():
    if shutil.which("mlx_whisper"):
        return ["mlx_whisper"], "mlx"
    if importlib.util.find_spec("mlx_whisper"):
        return [sys.executable, "-m", "mlx_whisper.cli"], "mlx"
    if shutil.which("whisper"):
        return ["whisper"], "openai"
    return None, None


def transcrever(arq, pasta_saida):
    """Um arquivo por vez (o mlx-whisper com vários de uma vez já trocou transcrição de nome)."""
    cmd, tipo = motor_whisper()
    if not cmd:
        return None, ("sem whisper instalado: rode `pip install mlx-whisper` (Mac M1+) ou "
                      "`pip install openai-whisper`, ou grave a transcrição em " + arq.stem + ".txt")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    if tipo == "mlx":
        modelo = os.environ.get("WHISPER_MODELO", "mlx-community/whisper-large-v3-turbo")
        cmd = cmd + [str(arq), "--model", modelo, "--language", "pt",
                     "--output-format", "txt", "--output-dir", str(pasta_saida)]
    else:
        modelo = os.environ.get("WHISPER_MODELO", "small")
        cmd = cmd + [str(arq), "--model", modelo, "--language", "pt",
                     "--output_format", "txt", "--output_dir", str(pasta_saida)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    saida = pasta_saida / (arq.stem + ".txt")
    if r.returncode != 0 or not saida.exists():
        return None, "whisper falhou: " + (r.stderr or r.stdout)[-300:]
    return saida.read_text(encoding="utf-8", errors="ignore"), None


def texto_do_arquivo(arq, transcrever_video=True):
    """Devolve (texto, origem, problema)."""
    ext = arq.suffix.lower()
    if ext in TEXTO:
        return arq.read_text(encoding="utf-8", errors="ignore"), "texto", None
    lado = arq.with_suffix(".txt")
    if lado.exists():
        return lado.read_text(encoding="utf-8", errors="ignore"), lado.name, None
    if ext in IMAGEM:
        return None, "imagem", f"leia o texto da arte e grave em {lado.name}"
    if ext in VIDEO:
        cache = arq.parent / ".transcricoes" / (arq.stem + ".txt")
        if cache.exists():
            return cache.read_text(encoding="utf-8", errors="ignore"), "transcrição (cache)", None
        if not transcrever_video:
            return None, "vídeo", f"sem transcrição: grave {lado.name} ou rode sem --sem-transcrever"
        texto, erro = transcrever(arq, arq.parent / ".transcricoes")
        return texto, "transcrição (whisper)", erro
    return None, "?", "formato que eu não leio"


def texto_da_pagina(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 checar-criativo"})
    with urllib.request.urlopen(req, timeout=20) as r:
        bruto = r.read().decode("utf-8", errors="ignore")
    bruto = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", bruto)
    titulo = re.search(r"(?is)<title[^>]*>(.*?)</title>", bruto)
    corpo = html.unescape(re.sub(r"(?s)<[^>]+>", " ", bruto))
    corpo = re.sub(r"\s+", " ", corpo)
    return ((titulo.group(1).strip() + " | ") if titulo else "") + corpo


def listar_arquivos(entradas):
    arquivos = []
    for e in entradas:
        p = Path(e).expanduser()
        if p.is_dir():
            todos = sorted(x for x in p.iterdir() if x.is_file() and not x.name.startswith("."))
            midias = {x.stem for x in todos if x.suffix.lower() in VIDEO | IMAGEM}
            for x in todos:
                ext = x.suffix.lower()
                if ext in VIDEO | IMAGEM:
                    arquivos.append(x)
                elif ext in TEXTO and x.stem not in midias:  # .txt ao lado da mídia não conta duas vezes
                    arquivos.append(x)
        elif p.is_file():
            arquivos.append(p)
        else:
            print(f"! não achei: {e}", file=sys.stderr)
    return arquivos


def imprimir(item):
    marca = {"FORA": "✗", "REVISAR": "!", "LIMPO": "✓", "PENDENTE": "?"}[item["veredito"]]
    print(f"\n{marca} {item['veredito']:<8} {item['item']}  ({item['origem']})")
    if item.get("problema"):
        print(f"    {item['problema']}")
    for a in item.get("achados", []):
        print(f"    [{a['severidade']}] {a['nome']}: \"{a['achou']}\"")
        print(f"           {a['trecho']}")


def main():
    ap = argparse.ArgumentParser(description="Checa criativo contra a política de publicidade da Meta antes de subir.")
    ap.add_argument("entradas", nargs="*", help="arquivos ou pastas (vídeo, imagem, .txt)")
    ap.add_argument("--copy", action="append", default=[], help="arquivo ou texto da copy/título/descrição (pode repetir)")
    ap.add_argument("--url", action="append", default=[], help="página de destino (pode repetir)")
    ap.add_argument("--texto", action="append", default=[], help="checa um texto solto")
    ap.add_argument("--termos", default=str(TERMOS), help="lista de termos (padrão: referencias/termos.json)")
    ap.add_argument("--sem-transcrever", action="store_true", help="não chama o whisper")
    ap.add_argument("--json", help="grava o resultado em JSON neste arquivo")
    args = ap.parse_args()

    if not (args.entradas or args.copy or args.url or args.texto):
        ap.print_help()
        return 1

    regras = carregar_regras(args.termos)
    itens = []

    def registrar(nome, origem, texto, problema=None):
        if texto is None:
            itens.append({"item": nome, "origem": origem, "veredito": "PENDENTE", "problema": problema})
            return
        ach = checar(texto, regras)
        itens.append({"item": nome, "origem": origem, "veredito": veredito(ach), "achados": ach})

    for arq in listar_arquivos(args.entradas):
        texto, origem, problema = texto_do_arquivo(arq, not args.sem_transcrever)
        registrar(arq.name, origem, texto, problema)
    for c in args.copy:
        p = Path(c).expanduser()
        if p.is_file():
            registrar(f"copy: {p.name}", "copy", p.read_text(encoding="utf-8", errors="ignore"))
        else:
            registrar(f"copy: {c[:40]}", "copy", c)
    for u in args.url:
        try:
            registrar(f"página: {u}", "página de destino", texto_da_pagina(u))
        except Exception as e:  # página fora do ar também é motivo de reprovação
            registrar(f"página: {u}", "página de destino", None, f"não abriu ({e})")
    for i, t in enumerate(args.texto, 1):
        registrar(f"texto {i}", "texto solto", t)

    print("Checagem de política · Meta Ads")
    for item in itens:
        imprimir(item)

    cont = {v: sum(1 for i in itens if i["veredito"] == v) for v in ("FORA", "REVISAR", "PENDENTE", "LIMPO")}
    print(f"\nResumo: {cont['FORA']} fora · {cont['REVISAR']} revisar · {cont['PENDENTE']} pendente · {cont['LIMPO']} limpo")
    print("O filtro acha palavra, não intenção: leia os trechos marcados no contexto antes de decidir.")

    if args.json:
        Path(args.json).write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
    if cont["FORA"]:
        return 2
    if cont["REVISAR"] or cont["PENDENTE"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
