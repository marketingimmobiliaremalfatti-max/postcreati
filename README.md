# Post brand – Immobiliare Malfatti

Genera post di fiducia/marketing (non legati a un singolo annuncio),
pensati per essere generati una tantum e riusati nel tempo su **Postpikr**.

## Come funziona

- `generate_brand_posts.py` legge i temi da `data/brand_topics.json`: ogni
  voce ha una domanda (mostrata nella bolla sopra la foto), l'URL di una
  foto di sfondo (licenza libera, uso commerciale consentito — attualmente
  da Unsplash) e il testo completo del post.
- Compone la foto con il template `assets/template_brand.png` (bolla
  bordeaux in alto a sinistra) scrivendoci dentro la domanda, con il font
  incluso in `assets/fonts/Poppins-Bold.ttf`.
- Genera `docs/brand-feed.xml`, da collegare a Postpikr come sorgente RSS.
- **Non gira in automatico**: il workflow è impostato solo su avvio
  manuale (`workflow_dispatch`). Lancialo quando aggiungi nuovi temi.

## Setup

1. Crea un repository **pubblico** su GitHub chiamato
   `malfatti-brand-posts` (o il nome che preferisci — se lo cambi,
   aggiorna `PAGES_BASE_URL` in `generate_brand_posts.py`).
2. Carica tutti i file di questo progetto (incluse le cartelle nascoste
   `.github/` e i file `.gitkeep` — se l'upload da browser non li
   trascina, creali a mano da **Add file → Create new file** scrivendo il
   percorso completo, es. `docs/brand-images/.gitkeep`).
3. **Settings → Pages**: Source `Deploy from a branch`, Branch `main`,
   cartella `/docs`.
4. **Settings → Actions → General**: "Read and write permissions" per i
   workflow.
5. Avvia il workflow manualmente: tab **Actions** → "Genera post brand
   Immobiliare Malfatti" → **Run workflow**.
6. Il feed sarà su:
   ```
   https://<tuo-utente-github>.github.io/<nome-repository>/brand-feed.xml
   ```
7. Incolla l'URL in Postpikr come sorgente separata da quella degli
   annunci, e salva/riusa i post da lì.

## Aggiungere nuovi temi

Il metodo di partenza (15 problemi ricorrenti dei venditori × 2 varianti
di titolo = 30 spunti, poi un post per ciascuno, max ~12 righe, tono
persuasivo ma informativo non promozionale) è quello che usa già
l'agenzia con ChatGPT. Per aggiungere un post, aggiungi una voce a
`data/brand_topics.json`:

```json
{
  "id": "brand-006",
  "quote": "Domanda breve per la bolla, con eventuale emoji",
  "image_url": "https://images.unsplash.com/photo-XXXX?fm=jpg&q=80&w=2000&auto=format&fit=crop",
  "caption": "Testo completo del post, con \n\n per gli a capo tra paragrafi."
}
```

Per le foto, cerca su [unsplash.com](https://unsplash.com) un'immagine
pertinente con licenza "Free to use under the Unsplash License" (non
quelle contrassegnate "Unsplash+", che sono a pagamento), apri la pagina
della foto e usa l'URL diretto dell'immagine (visibile nel tag
`og:image` della pagina, o cliccando con il tasto destro sull'immagine
grande → "Copia indirizzo immagine").
