---
name: checar-criativo
description: Checa criativo contra a política de publicidade da Meta ANTES de subir. Lê a fala do vídeo, o texto da arte, a copy, o título e a página de destino e devolve o que sobe, o que ajusta (com a frase reescrita) e o que fica de fora. Use quando o pedido for "checa esses criativos", "isso passa na Meta?", "antes de subir", "tá dentro da política?", "por que reprovou", "tomei reprovação", "tomei bloqueio", "a campanha parou depois que reprovou", ou antes de qualquer subida de anúncio.
---

# Checar criativo antes de subir

Toda reprovação fica no histórico da conta, e reprovação repetida vira restrição na conta e nos perfis
que administram a conta. Esta skill roda antes da subida. O script marca os trechos de risco e você
lê cada um no contexto e decide.

## Onde está o script

- Instalação global: `scripts/checar_criativo.py`, dentro da pasta desta skill.
- Aberto dentro do repositório `checar-criativo-meta`: `scripts/checar_criativo.py`, na raiz.

A lista de termos fica em `referencias/termos.json`, ao lado da pasta `scripts/`.

## Fluxo

1. **Junte tudo o que vai no anúncio.** Vídeos, imagens, texto principal, título, descrição e o link
   da página de destino. Faltou a copy ou a página? Peça ao usuário. A Meta lê tudo, e a página
   reprova o anúncio do mesmo jeito.
2. **Transforme cada peça em texto.**
   - Vídeo: o script transcreve sozinho com o whisper local e guarda em `<pasta>/.transcricoes/`. Se
     já houver `<nome>.txt` ao lado do vídeo, ele usa esse arquivo.
   - Imagem: abra a imagem, leia o texto escrito na arte, palavra por palavra, e grave em
     `<nome>.txt` ao lado dela. Sem esse arquivo, a imagem fica PENDENTE.
3. **Rode o script.**
   ```bash
   python3 <pasta>/scripts/checar_criativo.py <arquivos ou pastas> --copy <copy.txt ou "texto"> --url <página>
   ```
   `--copy` e `--url` podem repetir. `--texto "..."` checa uma frase solta. `--json saida.json` grava
   o resultado.
4. **Releia cada trecho marcado no contexto.** O script é uma peneira, e marcar não quer dizer
   reprovar.
   - "Presidente da associação" não é política. "O presidente aumentou o imposto" é.
   - "R$ 47 por mês" é preço. "R$ 300 por dia" como ganho é promessa.
   - "Aposta" de "aposto que você já viu isso" não é jogo de azar.
   - Item LIMPO também merece uma leitura rápida. O filtro não pega insinuação, imagem de antes e
     depois nem promessa feita sem número.
5. **Entregue a tabela.**

   | Criativo | Veredito | Trecho exato | Por quê | Reescrita |
   |---|---|---|---|---|
   | AD01 | SOBE | | | |
   | AD02 | AJUSTA | "você que está endividado" | atributo pessoal | "para quem quer sair das dívidas" |
   | AD03 | FORA | "Robux grátis" | golpe de moeda de jogo | sai, não tem reescrita |

   - **SOBE**: nada de risco depois da leitura.
   - **AJUSTA**: a frase exata, o motivo e a reescrita. Se o trecho está na fala do vídeo, diga o
     segundo aproximado e avise que precisa regravar ou cortar.
   - **FORA**: não sobe. Nunca suba criativo FORA, nem "para testar".

## Reescritas seguras

- Atributo pessoal → fale com quem quer mudar, não com quem está na condição: "você que está
  endividado" vira "para quem quer sair das dívidas"; "negocie sua dívida" vira "negocie dívidas".
- Promessa de ganho → mostre o processo, não o resultado: "ganhe R$ 300 por dia" vira "como eu faço,
  passo a passo". Sem valor de ganho, sem prazo, sem "garantido".
- Política → tire o político e deixe a ideia: "com o governo novo tomando posse, o mercado..." vira
  "com o mercado mudando...".
- Saúde → fale da rotina, não do corpo: "perdi 10 kg em 30 dias" vira "a rotina que eu sigo".
- Marca de terceiro (Roblox, Free Fire, Netflix) → evite o nome e a arte do jogo no criativo e não
  apele para criança. Moeda de jogo grátis, gerador e hack saem, sem reescrita.

## Se o usuário já tomou reprovação

- Não apagar o anúncio reprovado: apagar não limpa o histórico e tira a chance de pedir revisão.
- Corrigir o que a Meta apontou e reenviar para revisão, ou pedir revisão em
  facebook.com/accountquality se a reprovação foi injusta.
- Campanha parada depois de reprovações: antes de mexer em verba ou duplicar, abrir a Qualidade da
  Conta (facebook.com/accountquality) e ver se há restrição ou anúncio pendente.
- Rodar esta checagem nos criativos que ainda não subiram, porque a mesma frase costuma estar em
  vários.

## Ajustar a lista

Tomou reprovação por um termo que não estava na lista? Inclua em `referencias/termos.json` (regex
em minúsculo e sem acento). Antes de pôr um termo como ALTO, teste contra frase comum com
`--texto`: "partido" também é "quebrado", "ministra" também é "dá aula", "slots" também é "vagas".

A regra oficial: https://transparency.meta.com/policies/ad-standards/
