# checar-criativo-meta

Peneira que roda **antes** de subir anúncio no Meta. Lê tudo o que vai no anúncio (a fala do vídeo,
o texto da arte, a copy, o título e a página de destino) e marca o que costuma dar reprovação e,
quando repete, restrição na conta.

Roda sozinha no terminal, mas rende mais dentro do Claude Code ou do Codex. O script acha os
trechos, o agente lê cada um no contexto e te devolve três listas: o que sobe, o que ajusta (com a
frase reescrita) e o que fica de fora.

## Por que existe

Um cliente nosso ensina a vender boi na bolsa. Em ano de eleição, um anúncio dele falou em "governo
novo tomando posse". A Meta reprovou como tema político, os perfis que administravam a conta tomaram
restrição e a conta ficou um dia sem anunciar. Depois a gente achou a mesma frase em outros três
criativos que já estavam prontos para subir.

Desde então nada sobe sem passar por aqui. Na leva seguinte, de 21 vídeos, 12 ficaram de fora antes
de subir.

A Meta não reprova só palavra proibida. Ela também reprova quando o anúncio:

- afirma algo sobre quem está vendo ("você que está endividado");
- promete ganho ("R$ 300 por dia, sem esforço");
- toca em política ou em tema social sem o anunciante ter autorização;
- oferece moeda de jogo de graça ("Robux grátis");
- fala de aposta, de saúde com antes e depois, de cripto com rentabilidade.

E cada reprovação fica no histórico da conta.

## O que ele pega

| Veredito | Categoria | Exemplo |
|---|---|---|
| **FORA** | Política e eleição | "eleição", "urna", "governo novo tomando posse" |
| **FORA** | Promessa de ganho | "ganhe R$ 300", "dinheiro fácil", "renda garantida" |
| **FORA** | Atributo pessoal | "você que está endividado", "você que sofre de ansiedade" |
| **FORA** | Moeda de jogo grátis / hack | "Robux grátis", "gerador de diamantes", "mod menu" |
| **FORA** | Aposta | "bet", "cassino", "tigrinho" |
| **FORA** | Arma, droga, cigarro | "arma de fogo", "vape", "CBD" |
| REVISAR | Palavra que pode ser política | "presidente", "candidato", "prefeito" |
| REVISAR | Imposto e economia do país | "reforma tributária", "CBS", "inflação" |
| REVISAR | Valor por dia ou por mês | "R$ 300 por dia" (ganho?) × "R$ 1 por dia" (preço?) |
| REVISAR | Seu/sua + condição | "sua dívida", "seu nome sujo" |
| REVISAR | Jogo, marca de terceiro, público infantil | "Roblox", "Free Fire", "Minecraft" |
| REVISAR | Saúde e corpo | "antes e depois", "perdi 10 kg", "cura" |
| REVISAR | Cripto e produto financeiro | "bitcoin", "day trade", "empréstimo" |
| REVISAR | Sensacionalismo | "você não vai acreditar", "o que os bancos escondem" |
| REVISAR | Botão que não existe (em imagem) | "clique no play" |
| REVISAR | Palavrão | |

São 17 categorias e 136 padrões, todos em [`referencias/termos.json`](referencias/termos.json),
cada um com o porquê. Item sem nenhum trecho marcado sai como **LIMPO**. Item sem texto para ler (uma
imagem sem a transcrição da arte, por exemplo) sai como **PENDENTE**.

## Instalar

### Claude Code

```bash
git clone https://github.com/MatheusSBPRO/checar-criativo-meta.git
cd checar-criativo-meta
./instalar.sh --global
```

Com `--global`, a skill `checar-criativo` vale em qualquer pasta. Sem ele, ela só vale quando você
roda `claude` dentro desta pasta.

### Codex

Abra o Codex dentro da pasta (`cd checar-criativo-meta && codex`). Ele lê o [`AGENTS.md`](AGENTS.md)
sozinho. O `./instalar.sh --global` também copia a skill para `~/.codex/skills/`, se essa pasta
existir.

### Transcrição de vídeo

Para ler a fala do vídeo, o script usa o whisper rodando no seu computador:

- Mac com chip M1 ou mais novo: `pip install mlx-whisper`
- Outros: `pip install openai-whisper` (precisa do `ffmpeg`)

Sem whisper, deixe a transcrição num `.txt` com o mesmo nome do vídeo (`AD01.mp4` → `AD01.txt`).

O script só usa a biblioteca padrão do Python 3.9+. Fora o whisper, não tem nada para instalar.

## Usar

Dentro do Claude ou do Codex, é só pedir:

> checa esses criativos antes de subir: pasta `criativos/`, a copy está em `copy.txt` e a página é
> https://sua.pagina

Direto no terminal:

```bash
python3 scripts/checar_criativo.py criativos/                       # pasta inteira
python3 scripts/checar_criativo.py AD01.mp4 AD02.png --copy copy.txt --url https://sua.pagina
python3 scripts/checar_criativo.py --texto "Ganhe R$ 300 por dia jogando"
python3 scripts/checar_criativo.py criativos/ --json resultado.json  # para guardar
```

Código de saída: `2` se tiver FORA, `1` se tiver REVISAR ou PENDENTE e `0` se estiver tudo LIMPO.
Dá para usar como trava num processo automático.

## O fluxo

1. **Junte tudo o que vai no anúncio**: vídeo, arte, texto principal, título, descrição e o link da
   página. A Meta lê tudo isso, a página inclusive.
2. **Transforme em texto.** O vídeo passa pelo whisper. A imagem, o Claude ou o Codex lê e grava o
   texto da arte em `<nome>.txt`, ao lado dela.
3. **Rode o script.**
4. **Releia cada trecho marcado no contexto.** "Presidente da associação" não é política. "R$ 47 por
   mês" é preço, não ganho. O script é uma peneira e quem decide é a leitura.
5. **Entregue a tabela** SOBE / AJUSTA / FORA. No AJUSTA vão a frase exata e a reescrita. **FORA não
   sobe.**

## Reescritas que costumam passar

| Em vez de | Use |
|---|---|
| "Você que está endividado..." | "Para quem quer sair das dívidas..." |
| "Negocie sua dívida" | "Negocie dívidas" |
| "Ganhe R$ 300 por dia jogando" | Mostre o processo: "como eu faço, passo a passo". Sem valor de ganho e sem prazo |
| "Dinheiro fácil, sem esforço" | "Um método simples de seguir" |
| "Com o governo novo tomando posse, o mercado..." | "Com o mercado mudando..." (tira a política e fica a ideia) |
| "Perdi 10 kg em 30 dias" | "A rotina que eu sigo" |
| "Robux grátis" | Não tem reescrita. Sai. |

## Se já reprovou

- **Não apague o anúncio reprovado.** Apagar não limpa o histórico da conta, e você perde a chance de
  pedir revisão.
- **Corrija e reenvie.** Edite o que a Meta apontou e mande para revisão de novo. Se a reprovação foi
  injusta, peça revisão em [facebook.com/accountquality](https://www.facebook.com/accountquality).
- **Reprovação em sequência pesa.** Várias seguidas aumentam o risco de restrição na conta de anúncio
  e nos perfis que administram a conta.
- **Campanha parou depois de reprovações?** Antes de mexer em verba ou duplicar a campanha, abra a
  Qualidade da Conta (facebook.com/accountquality) e veja se há restrição ou anúncio pendente.

## Limites

- É uma peneira por palavras e frases. **LIMPO não garante aprovação.** A Meta também lê a imagem, a
  página e o comportamento da conta.
- A regra oficial, que manda em tudo: [Padrões de Publicidade da Meta](https://transparency.meta.com/policies/ad-standards/).
- A lista é sua. Tomou reprovação por um termo que não estava aqui? Coloque em
  `referencias/termos.json` (as instruções estão no próprio arquivo, em `_como_editar`). Antes de pôr
  um termo como ALTO, teste contra frase comum: "partido" também é "quebrado", "ministra" também é
  "dá aula".

## Licença

MIT. Veja [LICENCA.md](LICENCA.md).
