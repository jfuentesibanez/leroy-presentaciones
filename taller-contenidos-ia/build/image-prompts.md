# Illustration prompts — taller de IA para contenidos (Leroy Merlin)

18 ilustraciones, estilo anuncio de hogar años 50 / retrofuturismo atómico, con el verde Leroy como
único acento fuerte. Prompts en inglés (los modelos de imagen rinden mejor así).

**Cómo usarlos**
1. Genera `01-portada` **primero**: fija el estilo. Adjunta esa imagen a cada prompt siguiente y añade
   *"same illustrator, same palette, same line weight and halftone texture as the attached image"*.
   Es lo que evita que la serie se desvíe.
2. Cuadradas (1:1). Guarda cada una con el nombre del encabezado (`.png` vale) en una carpeta, p. ej.
   `~/Desktop/leroy-img/`, y ejecuta:
   ```bash
   cd build && python3 prepare-media.py ~/Desktop/leroy-img && python3 build.py
   ```
   `prepare-media.py` recorta al cuadrado si hace falta, iguala el fondo al papel #F7F4EE y escribe
   `img/` y `build/poster/`. Las diapositivas ya tienen `art=` puesto: en cuanto existe el archivo, aparece.
3. Si alguna sale con letras o un logo, regenérala: la regla de la casa es ninguna letra en las ilustraciones.

---

## STYLE BLOCK — pégalo delante de cada prompt

> Original mid-century American print advertisement illustration, 1950s atomic-age optimism, in the
> register of post-war home-appliance and hardware-store magazine ads and the retro-futurist look
> later borrowed by video games — but a new, original piece. Gouache and screen-print look: flat
> colour shapes, confident ink outlines, fine halftone dot texture in the shadows, a slight
> misregistration between colour plates, soft airbrushed highlights on chrome and enamel. Limited
> palette: cream, warm charcoal ink, faded turquoise, mustard yellow, small touches of coral red, and
> ONE strong accent green #78BE20 always on the key object of the image. People are cheerful,
> idealised 1950s figures with confident smiles, generic, never a real person and never an existing
> character or mascot. Robots are rounded 1950s robots in chrome and cream enamel, with dial faces,
> antennae and rivets, friendly rather than menacing. Plain flat background in ivory #F7F4EE, edge to
> edge, no gradient, no vignette, no frame or border, no scenery: one subject and at most two props.
> Absolutely no text, letters, numbers, logos, brand names or watermarks anywhere — labels, packaging,
> screens and signs are blank shapes. Square 1:1, print quality.

---

## 01-portada.png
Portada

A friendly chrome-and-cream 1950s robot in a hardware-store work apron, standing proudly and holding
up a paint roller in one hand and a blank product tag on a string in the other, like a salesman
presenting the product of the year. At its feet an open metal toolbox. The apron and the roller's
paint are accent green. Mood: optimistic, "the future of home improvement is here".

## 02-tres-modelos.png
*Qué significa para una ficha*

Three 1950s wooden-cabinet radio consoles of different sizes standing side by side — one small and
compact, one medium, one grand — each with glowing dial faces. A single sheet of paper feeds out
of the grandest one like a telegraph tape. The dial lights of all three are accent green. Mood: a
showroom of new machines.

## 03-voz.png
*La voz, lista para producción*

A 1950s woman in an apron speaking into a Bakelite telephone receiver held at arm's length, while
concentric sound rings float out of the earpiece and curve towards a chrome kitchen tap, which
answers with its own small rings. The telephone is accent green. Mood: talking to your house is
natural.

## 04-gafas.png
*Muse y las gafas*

A pair of thick horn-rimmed 1950s glasses floating in the air, with a tiny radar dish and antenna
on one temple arm. Through one lens we see a bathroom tap magnified, framed by a thin circular
targeting reticle drawn as simple lines. The antenna tip and reticle are accent green. Mood: the
assistant sees what you see.

## 05-anuncio.png
*ChatGPT Ads, ya en España*

A 1950s television set on tapered legs. On its screen, a cordless drill sits on a small velvet
pedestal under a spotlight, with a blank ribbon badge pinned to the pedestal. Beside the TV, a
smiling announcer-robot gestures at the screen with an open palm, like a game-show host. The drill
is accent green. Mood: a sponsored moment, clearly staged.

## 06-pregunta.png
*Ejercicio · 10 minutos*

A 1950s man in a cardigan leaning towards a desktop chrome console with a round speaker grille,
cupping his hand to his mouth as if asking a question. Floating between them, a blank empty speech
bubble outline containing only a simple drawing of a drill. The speech-bubble outline is accent
green. Mood: curiosity.

## 07-panel.png
*Tres preguntas antes de elegir*

A 1950s control panel on a steel desk: rows of toggle switches, three large round dials, and a big
lever with a knob. A single thick cable runs from the panel off the edge of the image. The lever
knob and one dial needle are accent green. Mood: you decide where things run.

## 08-cadena.png
*Caso: del brief a la ficha*

A small 1950s assembly-line machine in cream enamel: on the left a crumpled sheet of paper enters
a funnel; pistons and gears in the middle; on the right a neat, clean product card slides out onto
a tray, where a human hand holds a rubber stamp above it, about to approve. The rubber stamp is
accent green. Mood: the machine proposes, the person decides.

## 09-manual.png
*Paso 1 · Las instrucciones del agente*

A 1950s robot sitting on a stool, reading a thick instruction manual with blank pages, one finger
following a line, a pencil tucked behind its antenna. A second, thinner booklet (the tone guide)
rests on its knee. The manual's cover is accent green. Mood: studious, learning the house rules.

## 10-whatsapp.png
*Un cliente escribe por WhatsApp*

A 1950s woman in a bathroom doorway looking at a dark damp stain on the ceiling, typing on a small
chunky handheld device like a retro-futurist pager. Floating towards her, a friendly miniature
rocket carrying a paint can and a brush. The paint can is accent green. Mood: problem, then help
arrives.

## 11-foto.png
*O manda una foto*

A chunky 1950s instant camera photographing a broken chrome tap with a flash burst. Next to it,
a small robot hand holds up the exact matching spare part, perfectly aligned with the broken one.
The spare part is accent green. Mood: "that's the one you need".

## 12-ficha.png
*Qué le pide esto a contenidos*

A product blueprint of a shower screen, pinned to a drafting board: technical callout lines,
dimension arrows and a measuring tape unrolled along the bottom edge, with a pencil and a set
square. No numbers, the dimension marks are blank ticks. The measuring tape is accent green. Mood:
every attribute in its place.

## 13-taller.png
*Grupos y material*

A 1950s workshop bench seen from above at an angle: an open toolbox, a stack of blank product
sheets, a coffee cup, and a compact retro-futurist typewriter-terminal with a small round screen.
Four hands from different people reach in from the edges, working together. The terminal's screen
glow is accent green. Mood: team work.

## 14-lupa.png
*Paso 2 · La comprobación*

A large brass magnifying glass held over a product sheet, and next to the sheet an open supplier
catalogue. Thin dotted lines connect items on the sheet to items in the catalogue, each ending in
a small check-mark shape; one line ends in an empty circle instead: not yet verified.
The check marks are accent green. Mood: every fact traced to its source.

## 15-romper.png
*Paso 3 · Romperlo a propósito*

A comic 1950s robot tangled up in its own unrolled measuring tape, small sparks coming off one
antenna, while an old-fashioned alarm bell on the wall rings with vibration lines. The alarm bell is
accent green. Mood: funny failure, caught in time.

## 16-medir.png
*Qué medir antes de empezar*

A 1950s still life: a big chrome stopwatch, a folding carpenter's ruler and a round pressure gauge
with its needle in the middle, arranged like a product ad. The stopwatch's face ring is accent
green. Mood: measure first.

## 17-piloto.png
*Un piloto con nombre y apellidos*

A small 1950s rocket built from a paint can with fins, on a tiny launch pad, and a smiling person in
overalls holding a clipboard beside it, checking it before launch. The rocket's paint can is accent
green. Mood: a small, controlled first launch.

## 18-parada.png
*Criterio de parada*

A large mushroom-shaped emergency stop button on a yellow-and-charcoal striped industrial base, with
a gloved hand hovering just above it, ready. The button is coral red; the glove is accent green.
Mood: calm control, agreed in advance.
