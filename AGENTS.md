# Checar criativo antes de subir (Meta)

Este repositório checa criativo contra a política de publicidade da Meta antes de subir o anúncio.
Quando o usuário pedir para checar criativos, copy ou página, siga este fluxo. O detalhe completo está
em `.claude/skills/checar-criativo/SKILL.md`.

1. Junte tudo o que vai no anúncio: vídeos, imagens, texto principal, título, descrição e o link da
   página. Se faltar a copy ou a página, peça.
2. Vídeo: o script transcreve com o whisper local, ou usa `<nome>.txt` ao lado do vídeo. Imagem:
   leia o texto escrito na arte e grave em `<nome>.txt` ao lado dela (sem isso fica PENDENTE).
3. Rode:
   `python3 scripts/checar_criativo.py <arquivos ou pastas> --copy <arquivo ou "texto"> --url <página>`
4. Releia cada trecho marcado no contexto: "presidente da associação" não é política, "R$ 47 por
   mês" é preço e não ganho.
5. Entregue uma tabela SOBE / AJUSTA / FORA. No AJUSTA vão a frase exata, o motivo e a reescrita.
   Criativo FORA não sobe.

Reescritas seguras: "você que está endividado" → "para quem quer sair das dívidas"; valor de ganho →
mostrar o processo; política → tirar o político e manter a ideia; moeda de jogo grátis → sai.

Se já reprovou: não apagar o anúncio, corrigir e reenviar ou pedir revisão em
facebook.com/accountquality. Campanha parada depois de reprovações: olhar a Qualidade da Conta antes
de mexer em verba.
