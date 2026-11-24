# Créditos e dependências

- **MediaPipe Tasks Vision**, versão `0.10.22-rc.20250304`, Google. Distribuição: https://www.npmjs.com/package/@mediapipe/tasks-vision. Código: https://github.com/google-ai-edge/mediapipe. Licença Apache 2.0. Runtime e WASM vendorizados em `web/assets/vision`.
- **Face Landmarker**, float16, versão 1. Modelo distribuído por Google em https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task. Guia: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/web_js.
- **Face-API**, `@vladmandic/face-api` 1.7.15, MIT, https://github.com/vladmandic/face-api. Alternativa CPU com TensorFlow.js incluído (Apache 2.0), Tiny Face Detector e landmarks de 68 pontos. Somente detecção e geometria são usadas; não há identificação, reconhecimento ou inferências de idade/gênero/emoção. Arquivos e licença em `web/assets/facecpu`.
- **DM Sans**, Google Fonts, SIL Open Font License. https://github.com/google/fonts/tree/main/ofl/dmsans.
- **Foto de ambiente:** Unsplash, imagem `photo-1503951914875-452162b0f3f1`.
- **Referências de cortes:** Loicenzo Style / Fresha (https://www.fresha.com/a/loicenzo-style-rochdale-uk-135-drake-street-ohyduxfe); Evolve Barber Shop (https://www.evolvebarbershoptx.com/services); Unsplash (`photo-1621605815971-fbc98d665033` e `photo-1622296089863-eb7fc530daa8`). Imagens usadas como simulação conforme pedido; não atribuir à barbearia nem tratar como fotos próprias.

A classificação geométrica de tendência de formato e as recomendações do protótipo são heurísticas do projeto; não são uma funcionalidade de diagnóstico nem de identificação do MediaPipe.

## Referências de cortes da versão 3

- Textured crop: Haircode, https://haircode.com/articles/the-ultimate-guide-to-short-haircuts-for-men-finding-the-perfect-style/
- Low taper: Forte Series, https://forteseries.com/blogs/hairstyles/low-taper-fade
- Médio com franja: The Right Hairstyles, https://therighthairstyles.com/flattering-hairstyles-for-men/
- Side part: Mens Talk, https://mens-talk.online/hair/effective-medium-men-s-haircut-layers-ideas-for-a-stylish-look.html
- Crop com franja: Menfacts, https://menfacts.nl/wat-is-een-textured-crop-kapsel-de-ultieme-gids-voor-dit-stoere-en-stijlvolle-mannenkapsel/
- Cachos com fade: referência Pinterest, https://nz.pinterest.com/pin/449867450298592647/
- Afro com taper: referência Pinterest, https://www.pinterest.com/pin/308426274489230483/

São imagens de referência para simulação solicitada pelo usuário, com atribuição na interface. Não atribuir os trabalhos à Santo Bigode.

## Pacote de divulgação

As fotos citadas são fontes das telas demonstrativas. Os arquivos fotográficos foram omitidos do código público e substituídos por placeholders SVG próprios. Os modelos e suas licenças foram preservados. O projeto não declara uma licença própria geral para o código autoral neste pacote.
