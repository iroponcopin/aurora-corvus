#!/usr/bin/env python3
"""Builds cherry-controls/index.html -- how to fly Cherry's aircraft and sail its ships, in every language.

Owner (2026-09-23, IROHA, verbatim):

    飛行機と戦闘機の操作方法と船の操作方法を教えてください
    Corvus Webに公開してください

--------------------------------------------------------------------------
Why a page of its own, and not a section of /cherry/
--------------------------------------------------------------------------
The brand page says two things and nothing else (build_cherry.py, by the owner's
2026-09-10 word: 「ブランドの強さを説明するだけで良いです」「書くならプレミア感がある
文章を添えるだけです」), and its docstring keeps play guides off it. So the controls live
here, in the Cherry colours, and the brand page carries one quiet link to them (outside its
release block, whose single link check_cherry_release.py counts).

It sits at the top level (cherry-controls/, like known-issues/), not at cherry/controls/:
check_lang_switcher.py discovers the sections it audits one directory deep, and a page it
cannot see is a page no gate can fail for.

--------------------------------------------------------------------------
Where every fact comes from -- the mod's code, not memory
--------------------------------------------------------------------------
Read from the Cherry source that built the release in downloads/ (CONTROLS_FOR), and
checked claim by claim against that code by two independent reviews before publishing:
  * aircraft keys: client/aircraft/AircraftInput.java (R flaps, Z afterburner/reverse, U gear,
    Y doors, K hook, M next target, N radar mode, J fire, Left Alt free look, the arrows); W/S
    throttle, A/D rudder and Space brakes are the game's own movement keys; the radar cone,
    range and dwell: common/weapon/RadarLock; leaving, doors, fuel, loading: AircraftEntity;
  * ship keys: client/naval/VesselHelmInput.java (, . = - ; '), VesselStationInput.java (H),
    VesselGunneryInput.java, VesselChartScreen.java; the door rule: LargeVesselEntity;
  * item names and the two key categories: the mod's lang files. It ships en_us and ja_jp
    only, so every other language shows them in English in game -- and they are printed in
    English here, marked lang="en";
  * the menu path, Space, Left Alt / Left Option, Sneak, Movement and the hotbar: vanilla
    26.3's own lang files, per language, so the page names them the way the game does. On a
    Mac the game names Left Alt "Left Option" (InputQuirks.keyboardTranslationKey), so both
    are given.
  * 26.3 binds keys by SDL scancode -- a place on the keyboard -- and names each one by the
    player's layout (InputConstants$Type: SDL_GetKeyName(SDL_GetKeyFromScancode(...))). The
    page names keys by their place on a US keyboard and says so; the Japanese page adds the
    two JIS keys that differ ([=] is the ^ key, ['] the : key), since those are the ones a
    Japanese player would otherwise press in vain.

CONTROLS_FOR is the release whose code this was read from. A newer Cherry zip in downloads/
stops the build until the controls are read again against the new code and it is moved,
the way build_cherry.py's COPY_FOR guards the release line.

Markup inside the copy: [K] is a key cap (<kbd>). [SPACE], [LALT] and [LOPT] are the game's
own names for Space, Left Alt and Left Option in that language (KEYCAP). A pair of angle
brackets marks English text (lang="en"). Every language must carry exactly the English
shape, and the same keys in the same places (main() refuses anything else) -- so a
translation cannot move a key, drop one, or add one.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, asset_root_prefix, available_langs, esc, page, write_page,
)

SECTION = "cherry-controls/"
BRAND_SECTION = "cherry/"
CONTROLS_FOR = "1.1.2"
RELEASE_RE = re.compile(r"^Cherry_MODs_v(?P<ver>\d+(?:\.\d+)*)\+mc(?P<mc>\d+(?:\.\d+)*)\.zip$")

# The game's own names for the keys whose names are translated (vanilla 26.3 lang files).
KEYCAP = {
    "en": {"SPACE": "Space", "LALT": "Left Alt", "LOPT": "Left Option"},
    "ja": {"SPACE": "Space", "LALT": "左Alt", "LOPT": "左Option"},
    "es": {"SPACE": "Espacio", "LALT": "Alt izdo.", "LOPT": "Opción izq."},
    "fr": {"SPACE": "Espace", "LALT": "Alt", "LOPT": "Option gauche"},
    "zh": {"SPACE": "空格", "LALT": "左Alt", "LOPT": "左Option"},
    "ko": {"SPACE": "Space", "LALT": "왼쪽 Alt", "LOPT": "왼쪽 Option"},
    "pt-br": {"SPACE": "Espaço", "LALT": "Alt", "LOPT": "Option esq."},
    "it": {"SPACE": "Spazio", "LALT": "Alt", "LOPT": "Opz sinistro"},
    "ar": {"SPACE": "Space", "LALT": "Alt الأيسر", "LOPT": "Left Option"},
    "ru": {"SPACE": "Пробел", "LALT": "Alt слева", "LOPT": "Option слева"},
    "id": {"SPACE": "Spasi", "LALT": "Alt Kiri", "LOPT": "Option Kiri"},
    "de": {"SPACE": "Leertaste", "LALT": "Alt", "LOPT": "Wahltaste links"},
    "tr": {"SPACE": "Boşluk", "LALT": "Sol Alt", "LOPT": "Sol Option"},
}
# Every key the page may name. Anything else inside [...] stops the build.
KNOWN_KEYS = {"W", "A", "S", "D", "SPACE", "LALT", "LOPT", "R", "U", "Y", "K", "Z", "M", "N", "J",
              "↑", "↓", "←", "→", "H", ",", ".", "=", "-", ";", "'", "^", ":", "Q"}
# The keys the game's "Movement" category holds and the mod's own mappings; the English copy
# must name every one of them (a binding missing from the page stops the build).
MOD_KEYS = {"R", "Z", "U", "Y", "K", "M", "N", "J", "LALT", "↑", "↓", "←", "→",
            "H", ",", ".", "=", "-", ";", "'"}
MOVEMENT_KEYS = {"W", "A", "S", "D", "SPACE"}

# The game's own name for its movement key category (key.category.minecraft.movement).
MOVEMENT = {
    "ja": "移動", "en": "Movement", "es": "Movimiento", "fr": "Mouvements", "zh": "移动",
    "ko": "이동", "pt-br": "Movimentos", "it": "Movimento", "ar": "حركة", "ru": "Движение",
    "id": "Pergerakan", "de": "Bewegung", "tr": "Hareket",
}

# The in-game way to the key bindings, and the two Cherry key categories, as each language shows them.
PATH = {
    "ja": ("設定", "操作設定", "キー割り当て"),
    "en": ("Options", "Controls", "Key Binds"),
    "es": ("Opciones", "Controles", "Teclas"),
    "fr": ("Options", "Contrôles", "Assignation des touches"),
    "zh": ("选项", "按键控制", "按键绑定"),
    "ko": ("설정", "조작", "키 지정"),
    "pt-br": ("Opções", "Controles", "Atalhos"),
    "it": ("Opzioni", "Comandi", "Assegnazione dei tasti"),
    "ar": ("الخيارات", "التحكم", "روابط المفاتيح"),
    "ru": ("Настройки", "Управление", "Назначение клавиш"),
    "id": ("Opsi", "Kendali", "Tombol Pintas"),
    "de": ("Optionen", "Steuerung", "Tastenbelegung"),
    "tr": ("Ayarlar", "Kontroller", "Tuş Atamaları"),
}
CATEGORIES = {"ja": ("Cherry の飛行", "Cherry 艦の持ち場")}
CATEGORIES_EN = ("⟨Cherry Flight⟩", "⟨Cherry Ship Stations⟩")

# Each language: the heading, then the two cards. A card is a title, facts, a key table (action, how)
# and titled lists. Every language must have exactly the English shape, with the same keys in the same
# places (main() refuses anything else). Where 1.1.2 does not do what a key's name says, the copy says
# what it does and names the version -- and main() refuses a version here other than CONTROLS_FOR, so a
# line about one release cannot survive onto the next one's page.
CONTROLS = {
    "en": {
        "heading": "Controls",
        "air": {
            "title": "Aircraft — the Stratos-900 airliner and the Aegis-X fighter",
            "facts": [
                "Place: use the item on the ground where she has room; she stands there facing the way you look.",
                "Board: right-click the middle of the aircraft. The first aboard flies her (the Stratos-900 seats 18). Leave with Sneak; you cannot leave in the air.",
                "Fuel: on the ground, use a Propellant Canister on her, one per use.",
                "Recover: stopped on the ground with nobody aboard, hold Sneak and right-click her with an empty hand.",
            ],
            "keys": [
                ["Pitch and roll", "The mouse (up raises the nose, right rolls right) or [↑] [↓] [←] [→]. The stick eases back to centre as soon as the mouse stops or the key is released."],
                ["Throttle", "[W] more, [S] less. The lever stays where you leave it."],
                ["Rudder", "[A] / [D] (on the ground they steer the nose wheel too)."],
                ["Wheel brakes", "[SPACE]"],
                ["Look around", "Hold [LALT] (on a Mac, [LOPT]); meanwhile the mouse leaves the stick."],
                ["Flaps", "[R], one step per press; after the last step they go back up."],
                ["Landing gear", "[U]. It will not retract while the wheels carry weight."],
                ["Canopy / rear ramp", "[Y]: the Aegis-X canopy, the Stratos-900 rear ramp. They open only on the ground below 1 m/s and close by themselves once she moves off. The ramp is for show: board by right-clicking."],
                ["Arresting hook (Aegis-X)", "[K]"],
                ["Afterburner / reverse thrust", "[Z]: on the Aegis-X, the afterburner while held; without it, full throttle gives 60% of her thrust. On the Stratos-900, reverse thrust on or off; it pushes with the throttle, up to 40%."],
            ],
            "lists": [
                ["Take-off and landing", [
                    "Take-off: flaps out with [R], full throttle with [W] (on the Aegis-X, hold [Z] as well); at speed, raise the nose with the mouse, then raise the gear with [U].",
                    "Landing: throttle back with [S], gear down with [U], flaps out with [R]. After touchdown, brake with [SPACE]; on the Stratos-900, press [Z] and open the throttle with [W] for reverse thrust, and press [Z] again before the next take-off.",
                ]],
                ["Aegis-X weapons", [
                    "Load: use a Cherry Guided Missile on an Aegis-X on the ground, one per use. She carries two, and a new one comes loaded.",
                    "The radar watches 30° around the nose out to 512 blocks and locks the contact nearest the nose once it has held it for about 1.5 seconds. [N] switches between air and ground targets; [M] moves to the next contact, and the lock starts again.",
                    "[J] fires a missile at the locked target: in the air only, at most one a second.",
                ]],
            ],
        },
        "sea": {
            "title": "Ships — the Leviathan-Class ferry and the Dreadnought-Class destroyer",
            "facts": [
                "Place: use the item on the bottom, under water at least as deep as her draught along her whole length (3.5 m for the Leviathan-Class, 4 m for the Dreadnought-Class). The crosshair passes through water, so in deep water swim above the spot until the bottom is in reach. She floats there facing the way you look.",
                "Walk her decks and interiors. Stand at a station and press [H] to take it; press [H] again to leave. The chart table opens a screen instead: close it to leave.",
                "In 1.1.2 a ship cannot be turned back into an item in survival: the spot to click lies inside her hull, out of reach from off the deck.",
            ],
            "keys": [
                ["Rudder", "[,] and [.] turn the wheel; it stays where you leave it, and both together centre it. In 1.1.2 she turns the opposite way to their names and to the helm display: [,] swings the bow to starboard (right), [.] to port (left)."],
                ["Engine", "[=] ahead; [-] back towards stop. The lever stays where you leave it. In 1.1.2, astern (below 0) gives no thrust."],
                ["Heading hold", "[;] holds the heading she has when you press it, while the wheel is centred."],
                ["Instruments", "Shown above the hotbar while you are at the wheel."],
            ],
            "lists": [
                ["Chart table", [
                    "At the chart table, [H] opens the chart. Left-click adds a waypoint; the mouse wheel zooms.",
                    "Its buttons switch the autopilot on or off and clear the route. A leg across land or shallow water is refused. The autopilot only steers: set the engine ahead at the wheel, and it stops the engine at the last waypoint.",
                ]],
                ["Doors (Leviathan-Class)", [
                    "Stopped (under 0.3 m/s, engine at 0) and at the wheel, ['] opens and closes the bow visor and the ramps.",
                    "The engine gives no thrust until the doors are shut. The ramps can be walked on once fully down.",
                ]],
                ["CIC (Dreadnought-Class)", [
                    "Gunnery: both triple turrets train on the point you look at. Left-click fires a salvo, every 10 seconds; right-click launches the VLS at the target the radar has locked, once its hatch is open.",
                    "Sonar: ships, boats, swimmers and submerged contacts on a sweeping scope.",
                ]],
            ],
        },
    },
    "ja": {
        "heading": "操作方法",
        "air": {
            "title": "飛行機 —— 旅客機 Stratos-900 と戦闘機 Aegis-X",
            "facts": [
                "置く: 周りに余地のある地面にアイテムを使うと、見ている向きに機首を向けて止まります。",
                "乗る: 機体の真ん中を右クリック。最初に乗った人が操縦します(Stratos-900 は 18 席)。降りるのはスニークで、空中では降りられません。",
                "燃料: 地上で機体に「推進剤キャニスター」を使います。1 回に 1 缶です。",
                "回収: 地上で止まっていて誰も乗っていないとき、スニークしながら素手で右クリックします。",
            ],
            "keys": [
                ["機首上げ・下げ、ロール", "マウス(上で機首上げ、右で右ロール)または [↑] [↓] [←] [→]。マウスを止めるかキーを離すと、操縦桿はすぐ中央へ戻ります。"],
                ["推力", "[W] で上げる、[S] で下げる。レバーは離した位置に留まります。"],
                ["方向舵", "[A] / [D](地上では前輪も切ります)"],
                ["車輪のブレーキ", "[SPACE]"],
                ["見回す", "[LALT](Mac では [LOPT])を押している間。その間、マウスは操縦桿から外れます。"],
                ["フラップ", "[R] で 1 段ずつ。最後の段の次は上げに戻ります。"],
                ["脚", "[U]。車輪に重さが掛かっている間は上がりません。"],
                ["キャノピー / 後部ランプ", "[Y]: Aegis-X はキャノピー、Stratos-900 は後部ランプ。地上で 1 m/s 未満のときだけ開き、動き出すとひとりでに閉じます。ランプは見た目だけで、乗るのは右クリックです。"],
                ["着艦フック(Aegis-X)", "[K]"],
                ["アフターバーナー / 逆推力", "[Z]: Aegis-X は押している間アフターバーナー。これなしでは推力いっぱいでも 60% です。Stratos-900 は逆推力の入/切で、推力レバーに応じて最大 40% で押し戻します。"],
            ],
            "lists": [
                ["離陸と着陸", [
                    "離陸: [R] でフラップを出し、[W] で推力いっぱい(Aegis-X は [Z] も押し続ける)。速さが乗ったらマウスで機首を上げ、上がったら [U] で脚をしまいます。",
                    "着陸: [S] で推力を絞り、[U] で脚を出し、[R] でフラップ。接地したら [SPACE] でブレーキ。Stratos-900 は [Z] を押して [W] で推力を上げると逆推力が効きます。次の離陸の前に、もう一度 [Z] で戻してください。",
                ]],
                ["Aegis-X の兵装", [
                    "積む: 地上の Aegis-X に「Cherry 誘導ミサイル」を使うと、1 回に 1 発ずつ積めます。2 発まで積め、新しい機体は 2 発積んだ状態で出てきます。",
                    "レーダーは機首の前 30° 以内・512 ブロックまでを見て、機首にいちばん近い相手を約 1.5 秒捉え続けるとロックします。[N] で空と地上を切り替え、[M] で次の相手へ(ロックはやり直し)。",
                    "[J] で、ロックした目標へミサイルを撃ちます。空中でだけ、1 秒に 1 発までです。",
                ]],
            ],
        },
        "sea": {
            "title": "艦 —— Leviathan級フェリーと Dreadnought級駆逐艦",
            "facts": [
                "置く: 船体の長さにわたって喫水以上の深さ(Leviathan級 3.5 m、Dreadnought級 4 m)がある水の、水底にアイテムを使います。照準は水を素通りするので、深い所では水底に手が届くまでその上を泳いでください。見ている向きに船首を向けて浮かびます。",
                "甲板や艦内は歩けます。持ち場に立って [H] を押すと就き、もう一度 [H] で離れます。海図台は画面が開くので、閉じると離れます。",
                "1.1.2 では、サバイバルで艦をアイテムに戻せません。クリックする所が船体の中にあり、甲板の外からは届きません。",
            ],
            "keys": [
                ["舵", "[,] と [.] で舵輪を回します。離した位置に留まり、両方を同時に押すと中央に戻ります。1.1.2 では、艦はキーの名前と舵の表示とは逆に回ります: [,] で船首が右(面舵)へ、[.] で左(取舵)へ。"],
                ["機関", "[=] で前進、[-] で停止の側へ戻します。レバーは離した位置に留まります。1.1.2 では、後進(0 より下)にしても推力は出ません。"],
                ["方位の保持", "[;] で、押したときの方位を保ちます(舵輪が中央のあいだ)。"],
                ["計器", "舵輪に就いている間、ホットバーの上に出ます。"],
            ],
            "lists": [
                ["海図台", [
                    "海図台で [H] を押すと海図が開きます。左クリックで航路の点を足し、マウスホイールで縮尺を変えます。",
                    "ボタンで自動巡航の入/切と航路の消去。陸や浅瀬を横切る区間は断られます。自動巡航は舵を取るだけなので、機関は舵輪で前進にしておきます。最後の点で機関を止めます。",
                ]],
                ["扉(Leviathan級)", [
                    "止まっていて(0.3 m/s 未満、機関 0)舵輪に就いているとき、['] でバウバイザーとランプを開け閉めします。",
                    "扉が閉じきるまで機関は推力を出しません。ランプは下りきると歩けます。",
                ]],
                ["CIC(Dreadnought級)", [
                    "砲術席: 3 連装砲塔 2 基が、見ている点へ向きます。左クリックで斉射(10 秒ごと)、右クリックで、レーダーがロックした目標へ VLS(ハッチが開ききってから)。",
                    "ソナー席: 周りの艦、ボート、泳いでいる者、水中の相手を、回る走査の画面に映します。",
                ]],
            ],
        },
    },
    "es": {
        "heading": "Controles",
        "air": {
            "title": "Aeronaves: el avión de pasajeros Stratos-900 y el caza Aegis-X",
            "facts": [
                "Colocar: usa el objeto en el suelo, donde tenga espacio; queda ahí mirando hacia donde miras.",
                "Subir: haz clic derecho en el centro de la aeronave. Quien sube primero la pilota (el Stratos-900 tiene 18 asientos). Para bajar, «Agacharse»; en el aire no se puede.",
                "Combustible: en tierra, usa un ⟨Propellant Canister⟩ sobre ella, uno por uso.",
                "Recuperar: detenida en tierra y sin nadie a bordo, mantén «Agacharse» y haz clic derecho con la mano vacía.",
            ],
            "keys": [
                ["Cabeceo y alabeo", "El ratón (hacia arriba sube el morro, a la derecha alabea a la derecha) o [↑] [↓] [←] [→]. La palanca vuelve al centro en cuanto el ratón se detiene o sueltas la tecla."],
                ["Potencia", "[W] más, [S] menos. La palanca de gases se queda donde la dejas."],
                ["Timón de dirección", "[A] / [D] (en tierra también giran la rueda de morro)."],
                ["Frenos de las ruedas", "[SPACE]"],
                ["Mirar alrededor", "Mantén [LALT] (en Mac, [LOPT]); mientras tanto el ratón no mueve la palanca."],
                ["Flaps", "[R], un paso por pulsación; tras el último, se recogen."],
                ["Tren de aterrizaje", "[U]. No se recoge mientras las ruedas soportan peso."],
                ["Cabina / rampa trasera", "[Y]: la cubierta de la cabina del Aegis-X, la rampa trasera del Stratos-900. Solo se abren en tierra por debajo de 1 m/s y se cierran solas al ponerse en marcha. La rampa es decorativa: se sube con clic derecho."],
                ["Gancho de apontaje (Aegis-X)", "[K]"],
                ["Posquemador / inversión de empuje", "[Z]: en el Aegis-X, el posquemador mientras la mantienes; sin él, la potencia máxima da el 60 % del empuje. En el Stratos-900, activa o desactiva la inversión de empuje, que empuja según la palanca, hasta el 40 %."],
            ],
            "lists": [
                ["Despegue y aterrizaje", [
                    "Despegue: flaps con [R], potencia máxima con [W] (en el Aegis-X, mantén también [Z]); con velocidad, sube el morro con el ratón y luego recoge el tren con [U].",
                    "Aterrizaje: reduce con [S], baja el tren con [U] y saca los flaps con [R]. Tras tocar tierra, frena con [SPACE]; en el Stratos-900, pulsa [Z] y abre gases con [W] para invertir el empuje, y vuelve a pulsar [Z] antes del siguiente despegue.",
                ]],
                ["Armamento del Aegis-X", [
                    "Cargar: usa un ⟨Cherry Guided Missile⟩ sobre un Aegis-X en tierra, uno por uso. Lleva dos, y uno nuevo llega cargado.",
                    "El radar vigila 30° alrededor del morro hasta 512 bloques y fija el contacto más cercano al morro tras mantenerlo unos 1,5 segundos. [N] alterna entre objetivos aéreos y terrestres; [M] pasa al siguiente contacto y la fijación empieza de nuevo.",
                    "[J] dispara un misil al objetivo fijado: solo en el aire, como mucho uno por segundo.",
                ]],
            ],
        },
        "sea": {
            "title": "Buques: el transbordador clase Leviathan y el destructor clase Dreadnought",
            "facts": [
                "Colocar: usa el objeto sobre el fondo, bajo agua al menos tan profunda como su calado a lo largo de toda su eslora (3,5 m el clase Leviathan, 4 m el clase Dreadnought). La mira atraviesa el agua, así que en aguas profundas nada sobre el lugar hasta alcanzar el fondo. Flota ahí mirando hacia donde miras.",
                "Recorre sus cubiertas e interiores. Ponte en un puesto y pulsa [H] para ocuparlo; pulsa [H] otra vez para dejarlo. La mesa de cartas abre una pantalla: ciérrala para dejarla.",
                "En 1.1.2 un buque no puede volver a ser un objeto en supervivencia: el punto donde hay que hacer clic está dentro del casco, fuera de alcance desde fuera de la cubierta.",
            ],
            "keys": [
                ["Timón", "[,] y [.] mueven la rueda; se queda donde la dejas y las dos a la vez la centran. En 1.1.2 el buque gira al revés que sus nombres y que la indicación del timón: [,] lleva la proa a estribor (derecha), [.] a babor (izquierda)."],
                ["Máquina", "[=] avante; [-] de vuelta hacia parada. La palanca se queda donde la dejas. En 1.1.2, atrás (por debajo de 0) no da empuje."],
                ["Mantener el rumbo", "[;] mantiene el rumbo que tiene al pulsarla, mientras la rueda esté centrada."],
                ["Instrumentos", "Aparecen sobre la barra de acceso rápido mientras estás al timón."],
            ],
            "lists": [
                ["Mesa de cartas", [
                    "En la mesa de cartas, [H] abre la carta. El clic izquierdo añade un punto de ruta; la rueda del ratón cambia la escala.",
                    "Sus botones conectan o desconectan el piloto automático y borran la ruta. Un tramo que cruza tierra o aguas someras se rechaza. El piloto automático solo gobierna: pon la máquina avante al timón; en el último punto la para.",
                ]],
                ["Puertas (clase Leviathan)", [
                    "Detenido (menos de 0,3 m/s, máquina en 0) y al timón, ['] abre y cierra la visera de proa y las rampas.",
                    "La máquina no da empuje hasta que las puertas están cerradas. Las rampas se pueden pisar cuando han bajado del todo.",
                ]],
                ["CIC (clase Dreadnought)", [
                    "Artillería: las dos torres triples apuntan al punto que miras. El clic izquierdo dispara una salva, cada 10 segundos; el derecho lanza el VLS contra el objetivo fijado por el radar, una vez abierta su escotilla.",
                    "Sonar: buques, botes, nadadores y contactos sumergidos en una pantalla de barrido.",
                ]],
            ],
        },
    },
    "fr": {
        "heading": "Commandes",
        "air": {
            "title": "Avions : l’avion de ligne Stratos-900 et le chasseur Aegis-X",
            "facts": [
                "Poser : utilisez l’objet sur le sol, là où il a la place ; l’avion s’y pose face à la direction de votre regard.",
                "Monter : clic droit sur le milieu de l’avion. Le premier à monter pilote (le Stratos-900 a 18 places). Pour descendre, « S’accroupir » ; impossible en vol.",
                "Carburant : au sol, utilisez un ⟨Propellant Canister⟩ sur l’avion, un par utilisation.",
                "Récupérer : à l’arrêt au sol et sans personne à bord, maintenez « S’accroupir » et faites un clic droit à main nue.",
            ],
            "keys": [
                ["Tangage et roulis", "La souris (vers le haut : cabrer, vers la droite : roulis à droite) ou [↑] [↓] [←] [→]. Le manche revient au centre dès que la souris s’arrête ou que la touche est relâchée."],
                ["Poussée", "[W] plus, [S] moins. La manette reste où vous la laissez."],
                ["Gouverne de direction", "[A] / [D] (au sol, elles orientent aussi la roulette de nez)."],
                ["Freins de roues", "[SPACE]"],
                ["Regarder autour", "Maintenez [LALT] (sur Mac, [LOPT]) ; pendant ce temps la souris quitte le manche."],
                ["Volets", "[R], un cran par appui ; après le dernier, ils rentrent."],
                ["Train d’atterrissage", "[U]. Il ne rentre pas tant que les roues portent du poids."],
                ["Verrière / rampe arrière", "[Y] : la verrière de l’Aegis-X, la rampe arrière du Stratos-900. Elles ne s’ouvrent qu’au sol sous 1 m/s et se referment d’elles-mêmes dès que l’avion roule. La rampe est décorative : on monte par clic droit."],
                ["Crosse d’appontage (Aegis-X)", "[K]"],
                ["Postcombustion / inversion de poussée", "[Z] : sur l’Aegis-X, la postcombustion tant qu’elle est maintenue ; sans elle, la pleine poussée ne donne que 60 %. Sur le Stratos-900, active ou coupe l’inversion de poussée, qui pousse selon la manette, jusqu’à 40 %."],
            ],
            "lists": [
                ["Décollage et atterrissage", [
                    "Décollage : volets avec [R], pleine poussée avec [W] (sur l’Aegis-X, maintenez aussi [Z]) ; une fois lancé, cabrez à la souris, puis rentrez le train avec [U].",
                    "Atterrissage : réduisez avec [S], sortez le train avec [U] et les volets avec [R]. Après le toucher, freinez avec [SPACE] ; sur le Stratos-900, appuyez sur [Z] puis remettez les gaz avec [W] pour inverser la poussée, et rappuyez sur [Z] avant le décollage suivant.",
                ]],
                ["Armement de l’Aegis-X", [
                    "Charger : utilisez un ⟨Cherry Guided Missile⟩ sur un Aegis-X au sol, un par utilisation. Il en emporte deux, et un neuf arrive chargé.",
                    "Le radar surveille 30° autour du nez jusqu’à 512 blocs et verrouille le contact le plus proche du nez après l’avoir gardé environ 1,5 seconde. [N] bascule entre cibles aériennes et au sol ; [M] passe au contact suivant et le verrouillage recommence.",
                    "[J] tire un missile sur la cible verrouillée : en vol seulement, au plus un par seconde.",
                ]],
            ],
        },
        "sea": {
            "title": "Navires : le transbordeur classe Leviathan et le destroyer classe Dreadnought",
            "facts": [
                "Poser : utilisez l’objet sur le fond, sous une eau au moins aussi profonde que son tirant d’eau sur toute sa longueur (3,5 m pour la classe Leviathan, 4 m pour la classe Dreadnought). Le viseur traverse l’eau : en eau profonde, nagez au-dessus de l’endroit jusqu’à atteindre le fond. Le navire y flotte, face à la direction de votre regard.",
                "Parcourez ses ponts et ses intérieurs. Placez-vous à un poste et appuyez sur [H] pour le prendre ; appuyez de nouveau sur [H] pour le quitter. La table à cartes ouvre un écran : fermez-le pour la quitter.",
                "En 1.1.2, un navire ne peut pas redevenir un objet en survie : l’endroit à cliquer se trouve dans la coque, hors de portée depuis l’extérieur du pont.",
            ],
            "keys": [
                ["Barre", "[,] et [.] tournent la roue ; elle reste où vous la laissez et les deux ensemble la remettent au centre. En 1.1.2, le navire tourne à l’inverse de leur nom et de l’affichage de la barre : [,] porte l’étrave sur tribord (droite), [.] sur bâbord (gauche)."],
                ["Machine", "[=] en avant ; [-] revient vers l’arrêt. La manette reste où vous la laissez. En 1.1.2, la marche arrière (sous 0) ne donne aucune poussée."],
                ["Tenue de cap", "[;] tient le cap qu’il a quand vous appuyez, tant que la roue est au centre."],
                ["Instruments", "Affichés au-dessus de la barre d’action tant que vous êtes à la barre."],
            ],
            "lists": [
                ["Table à cartes", [
                    "À la table à cartes, [H] ouvre la carte. Le clic gauche ajoute un point de route ; la molette change l’échelle.",
                    "Ses boutons engagent ou coupent le pilote automatique et effacent la route. Un tronçon qui traverse la terre ou des hauts-fonds est refusé. Le pilote automatique ne fait que barrer : mettez la machine en avant à la barre ; il l’arrête au dernier point.",
                ]],
                ["Portes (classe Leviathan)", [
                    "À l’arrêt (moins de 0,3 m/s, machine à 0) et à la barre, ['] ouvre et ferme la visière d’étrave et les rampes.",
                    "La machine ne pousse pas tant que les portes ne sont pas fermées. On peut marcher sur les rampes une fois entièrement abaissées.",
                ]],
                ["CIC (classe Dreadnought)", [
                    "Poste de tir : les deux tourelles triples pointent vers l’endroit que vous regardez. Le clic gauche tire une salve, toutes les 10 secondes ; le clic droit lance le VLS sur la cible verrouillée par le radar, une fois sa trappe ouverte.",
                    "Sonar : navires, embarcations, nageurs et contacts immergés sur un écran à balayage.",
                ]],
            ],
        },
    },
    "zh": {
        "heading": "操作方法",
        "air": {
            "title": "飞机：客机 Stratos-900 与战斗机 Aegis-X",
            "facts": [
                "放置：在有足够空间的地面上使用该物品，飞机会停在那里，机头朝向你注视的方向。",
                "登机：右键点击飞机中部。第一个登机的人驾驶（Stratos-900 有 18 个座位）。按“潜行”离机；在空中无法离机。",
                "燃料：在地面上对飞机使用⟨Propellant Canister⟩，每次一罐。",
                "回收：飞机停在地面且无人乘坐时，按住“潜行”并空手右键点击。",
            ],
            "keys": [
                ["俯仰与横滚", "鼠标（向上抬机头，向右右滚转）或 [↑] [↓] [←] [→]。鼠标一停下或松开按键，操纵杆就会回中。"],
                ["推力", "[W] 增加，[S] 减少。油门杆停在你松开的位置。"],
                ["方向舵", "[A] / [D]（在地面上也会转动前轮）"],
                ["机轮刹车", "[SPACE]"],
                ["环顾四周", "按住 [LALT]（Mac 上为 [LOPT]）；此时鼠标不控制操纵杆。"],
                ["襟翼", "[R] 每按一次放下一档；最后一档之后收起。"],
                ["起落架", "[U]。机轮承重时不会收起。"],
                ["座舱盖 / 尾部跳板", "[Y]：Aegis-X 为座舱盖，Stratos-900 为尾部跳板。只有在地面上且低于 1 m/s 时才能打开，飞机一动就会自动关闭。跳板仅为外观，登机请右键点击。"],
                ["着舰钩（Aegis-X）", "[K]"],
                ["加力 / 反推", "[Z]：Aegis-X 按住时开启加力；不开加力时，满油门只有 60% 推力。Stratos-900 切换反推开关，反推随油门增加，最高 40%。"],
            ],
            "lists": [
                ["起飞与降落", [
                    "起飞：按 [R] 放襟翼，按 [W] 推满油门（Aegis-X 还要按住 [Z]）；速度足够后用鼠标抬起机头，再按 [U] 收起落架。",
                    "降落：按 [S] 收油门，按 [U] 放起落架，按 [R] 放襟翼。接地后按 [SPACE] 刹车；Stratos-900 可按 [Z] 后用 [W] 加油门来反推，下次起飞前再按一次 [Z] 关闭。",
                ]],
                ["Aegis-X 的武器", [
                    "装填：对地面上的 Aegis-X 使用⟨Cherry Guided Missile⟩，每次装一枚。最多两枚，新飞机自带两枚。",
                    "雷达监视机头周围 30° 以内、512 格以内的范围，持续捕捉离机头最近的目标约 1.5 秒后锁定。[N] 切换对空与对地，[M] 换到下一个目标并重新锁定。",
                    "[J] 向锁定的目标发射导弹：仅限空中，每秒最多一枚。",
                ]],
            ],
        },
        "sea": {
            "title": "舰船：Leviathan 级渡轮与 Dreadnought 级驱逐舰",
            "facts": [
                "放置：对水底使用该物品，整个船身长度上的水深都要不小于吃水（Leviathan 级 3.5 m，Dreadnought 级 4 m）。准星会穿过水面，所以在深水处要游到该位置上方，直到够得着水底。舰船会浮在那里，船首朝向你注视的方向。",
                "可以在甲板和舱内行走。站在岗位处按 [H] 就位，再按一次 [H] 离开。海图桌会打开一个界面：关闭它即离开。",
                "在 1.1.2 中，生存模式下无法把舰船收回成物品：需要点击的位置在船体内部，从甲板以外够不着。",
            ],
            "keys": [
                ["舵", "[,] 和 [.] 转动舵轮；舵轮停在你松开的位置，两键同时按下回正。在 1.1.2 中，舰船的转向与按键名称和舵角显示相反：[,] 使船首转向右舷（右），[.] 转向左舷（左）。"],
                ["主机", "[=] 前进；[-] 回到停车方向。车钟停在你松开的位置。在 1.1.2 中，后退（低于 0）不产生推力。"],
                ["保持航向", "[;] 保持按下时的航向（舵轮回中期间）。"],
                ["仪表", "在舵轮岗位时显示在快捷栏上方。"],
            ],
            "lists": [
                ["海图桌", [
                    "在海图桌按 [H] 打开海图。左键添加航路点，鼠标滚轮缩放。",
                    "按钮可开关自动航行、清除航线。穿越陆地或浅水的航段会被拒绝。自动航行只负责操舵：请先在舵轮处把主机设为前进；到达最后一个航路点时它会停车。",
                ]],
                ["舱门（Leviathan 级）", [
                    "停船（低于 0.3 m/s、主机为 0）并在舵轮岗位时，按 ['] 开关艏门和跳板。",
                    "舱门完全关闭前主机不会产生推力。跳板完全放下后可以在上面行走。",
                ]],
                ["CIC（Dreadnought 级）", [
                    "火炮岗位：两座三联装炮塔指向你注视的位置。左键齐射，每 10 秒一次；右键在舱盖打开后，向雷达锁定的目标发射垂直发射系统。",
                    "声呐岗位：在扫描屏上显示周围的舰船、小船、游泳者和水下目标。",
                ]],
            ],
        },
    },
    "ko": {
        "heading": "조작 방법",
        "air": {
            "title": "항공기: 여객기 Stratos-900과 전투기 Aegis-X",
            "facts": [
                "놓기: 공간이 충분한 땅에 아이템을 사용하면 그 자리에 바라보는 방향으로 기수를 두고 섭니다.",
                "탑승: 기체의 한가운데를 오른쪽 클릭합니다. 먼저 탄 사람이 조종합니다(Stratos-900은 18석). 내릴 때는 ‘웅크리기’를 누르며, 공중에서는 내릴 수 없습니다.",
                "연료: 지상에서 기체에 ⟨Propellant Canister⟩를 사용합니다. 한 번에 하나씩입니다.",
                "회수: 지상에 멈춰 있고 아무도 타지 않았을 때, ‘웅크리기’를 누른 채 맨손으로 오른쪽 클릭합니다.",
            ],
            "keys": [
                ["피치와 롤", "마우스(위로 기수 올림, 오른쪽으로 오른쪽 롤) 또는 [↑] [↓] [←] [→]. 마우스가 멈추거나 키를 떼면 조종간은 곧바로 중앙으로 돌아옵니다."],
                ["추력", "[W] 올림, [S] 내림. 레버는 놓은 자리에 머뭅니다."],
                ["방향타", "[A] / [D] (지상에서는 앞바퀴도 돌립니다)"],
                ["바퀴 브레이크", "[SPACE]"],
                ["둘러보기", "[LALT](Mac에서는 [LOPT])를 누르는 동안. 그동안 마우스는 조종간에서 떨어집니다."],
                ["플랩", "[R]을 누를 때마다 한 단계. 마지막 단계 다음에는 올라갑니다."],
                ["착륙 장치", "[U]. 바퀴에 무게가 실린 동안에는 올라가지 않습니다."],
                ["캐노피 / 후방 램프", "[Y]: Aegis-X는 캐노피, Stratos-900은 후방 램프. 지상에서 1 m/s 미만일 때만 열리고, 움직이기 시작하면 저절로 닫힙니다. 램프는 겉모습뿐이며, 탑승은 오른쪽 클릭으로 합니다."],
                ["착함 훅(Aegis-X)", "[K]"],
                ["애프터버너 / 역추력", "[Z]: Aegis-X는 누르는 동안 애프터버너. 이것 없이는 추력을 최대로 해도 60%입니다. Stratos-900은 역추력 켜기/끄기로, 추력 레버에 따라 최대 40%로 밀어냅니다."],
            ],
            "lists": [
                ["이륙과 착륙", [
                    "이륙: [R]로 플랩을 내리고 [W]로 추력을 최대로(Aegis-X는 [Z]도 누른 채로). 속도가 붙으면 마우스로 기수를 들고 [U]로 착륙 장치를 올립니다.",
                    "착륙: [S]로 추력을 줄이고 [U]로 착륙 장치를, [R]로 플랩을 내립니다. 접지 후 [SPACE]로 브레이크. Stratos-900은 [Z]를 누르고 [W]로 추력을 올리면 역추력이 걸리며, 다음 이륙 전에 [Z]를 다시 눌러 끕니다.",
                ]],
                ["Aegis-X 무장", [
                    "장전: 지상의 Aegis-X에 ⟨Cherry Guided Missile⟩를 사용하면 한 번에 한 발씩 실립니다. 두 발까지 실리며, 새 기체는 두 발을 실은 채 나옵니다.",
                    "레이더는 기수 주위 30° 이내, 512블록까지를 살피고, 기수에 가장 가까운 상대를 약 1.5초 동안 잡아 두면 고정합니다. [N]은 공중/지상 목표 전환, [M]은 다음 상대로 넘어가며 고정을 다시 시작합니다.",
                    "[J]로 고정한 목표에 미사일을 발사합니다. 공중에서만, 1초에 한 발까지입니다.",
                ]],
            ],
        },
        "sea": {
            "title": "함정: Leviathan급 카페리와 Dreadnought급 구축함",
            "facts": [
                "놓기: 선체 길이 전체에 걸쳐 흘수 이상으로 깊은 물(Leviathan급 3.5 m, Dreadnought급 4 m)의 바닥에 아이템을 사용합니다. 조준선은 물을 통과하므로, 깊은 곳에서는 바닥에 손이 닿을 때까지 그 위를 헤엄치세요. 바라보는 방향으로 선수를 두고 뜹니다.",
                "갑판과 선내를 걸어 다닐 수 있습니다. 근무 위치에 서서 [H]를 누르면 맡고, [H]를 다시 누르면 떠납니다. 해도대는 화면이 열리므로, 닫으면 떠납니다.",
                "1.1.2에서는 서바이벌에서 함정을 아이템으로 되돌릴 수 없습니다. 클릭해야 할 곳이 선체 안에 있어 갑판 밖에서는 닿지 않습니다.",
            ],
            "keys": [
                ["조타", "[,]와 [.]로 타륜을 돌립니다. 놓은 자리에 머물고, 둘을 함께 누르면 중앙으로 돌아옵니다. 1.1.2에서는 함정이 키 이름과 타각 표시와 반대로 돕니다: [,]는 선수를 우현(오른쪽)으로, [.]는 좌현(왼쪽)으로 돌립니다."],
                ["기관", "[=] 전진, [-] 정지 쪽으로 되돌림. 레버는 놓은 자리에 머뭅니다. 1.1.2에서는 후진(0 아래)으로 해도 추력이 나오지 않습니다."],
                ["침로 유지", "[;] 누른 때의 침로를 유지합니다(타륜이 중앙인 동안)."],
                ["계기", "타륜을 맡은 동안 단축 바 위에 표시됩니다."],
            ],
            "lists": [
                ["해도대", [
                    "해도대에서 [H]를 누르면 해도가 열립니다. 왼쪽 클릭으로 항로점을 추가하고, 마우스 휠로 축척을 바꿉니다.",
                    "버튼으로 자동 항해를 켜고 끄며 항로를 지웁니다. 육지나 얕은 물을 가로지르는 구간은 거부됩니다. 자동 항해는 키만 잡으므로, 타륜에서 기관을 전진으로 해 두세요. 마지막 항로점에서 기관을 멈춥니다.",
                ]],
                ["문(Leviathan급)", [
                    "멈춰 있고(0.3 m/s 미만, 기관 0) 타륜을 맡았을 때 [']로 선수 바이저와 램프를 여닫습니다.",
                    "문이 완전히 닫힐 때까지 기관은 추력을 내지 않습니다. 램프는 완전히 내려가면 걸을 수 있습니다.",
                ]],
                ["CIC(Dreadnought급)", [
                    "포술 위치: 3연장 포탑 2기가 바라보는 지점을 겨눕니다. 왼쪽 클릭으로 일제사격(10초마다), 오른쪽 클릭으로 해치가 열린 뒤 레이더가 고정한 목표에 VLS를 발사합니다.",
                    "소나 위치: 주변의 함정, 보트, 헤엄치는 사람과 수중 목표를 회전 탐색 화면에 표시합니다.",
                ]],
            ],
        },
    },
    "pt-br": {
        "heading": "Controles",
        "air": {
            "title": "Aeronaves: o avião de passageiros Stratos-900 e o caça Aegis-X",
            "facts": [
                "Posicionar: use o item no chão, onde houver espaço; a aeronave fica ali, virada para onde você olha.",
                "Embarcar: clique com o botão direito no meio da aeronave. Quem embarca primeiro pilota (o Stratos-900 tem 18 assentos). Para desembarcar, use “Agachar”; no ar não é possível.",
                "Combustível: no chão, use um ⟨Propellant Canister⟩ na aeronave, um por uso.",
                "Recolher: parada no chão e sem ninguém a bordo, segure “Agachar” e clique com o botão direito de mão vazia.",
            ],
            "keys": [
                ["Arfagem e rolagem", "O mouse (para cima levanta o nariz, para a direita rola à direita) ou [↑] [↓] [←] [→]. O manche volta ao centro assim que o mouse para ou a tecla é solta."],
                ["Potência", "[W] mais, [S] menos. A manete fica onde você deixar."],
                ["Leme de direção", "[A] / [D] (no chão, também viram a roda do nariz)."],
                ["Freios das rodas", "[SPACE]"],
                ["Olhar ao redor", "Segure [LALT] (no Mac, [LOPT]); enquanto isso o mouse não move o manche."],
                ["Flaps", "[R], um estágio por toque; depois do último, recolhidos."],
                ["Trem de pouso", "[U]. Não recolhe enquanto as rodas sustentam peso."],
                ["Canopi / rampa traseira", "[Y]: o canopi do Aegis-X, a rampa traseira do Stratos-900. Só abrem no chão abaixo de 1 m/s e fecham sozinhos quando a aeronave se move. A rampa é só visual: embarque com o botão direito."],
                ["Gancho de pouso (Aegis-X)", "[K]"],
                ["Pós-combustor / reverso", "[Z]: no Aegis-X, o pós-combustor enquanto segurar; sem ele, a potência máxima dá 60% do empuxo. No Stratos-900, liga ou desliga o reverso, que empurra conforme a manete, até 40%."],
            ],
            "lists": [
                ["Decolagem e pouso", [
                    "Decolagem: flaps com [R], potência máxima com [W] (no Aegis-X, segure também [Z]); com velocidade, levante o nariz com o mouse e depois recolha o trem com [U].",
                    "Pouso: reduza com [S], baixe o trem com [U] e os flaps com [R]. Depois de tocar o solo, freie com [SPACE]; no Stratos-900, aperte [Z] e acelere com [W] para usar o reverso, e aperte [Z] de novo antes da próxima decolagem.",
                ]],
                ["Armamento do Aegis-X", [
                    "Carregar: use um ⟨Cherry Guided Missile⟩ num Aegis-X no chão, um por uso. Ele leva dois, e um novo já vem carregado.",
                    "O radar vigia 30° em torno do nariz até 512 blocos e trava o contato mais próximo do nariz depois de mantê-lo por cerca de 1,5 segundo. [N] alterna entre alvos aéreos e terrestres; [M] passa ao próximo contato e a trava recomeça.",
                    "[J] dispara um míssil no alvo travado: só no ar, no máximo um por segundo.",
                ]],
            ],
        },
        "sea": {
            "title": "Navios: o ferry classe Leviathan e o contratorpedeiro classe Dreadnought",
            "facts": [
                "Posicionar: use o item no fundo, sob água pelo menos tão funda quanto o calado ao longo de todo o casco (3,5 m no classe Leviathan, 4 m no classe Dreadnought). A mira atravessa a água, então em água funda nade sobre o local até alcançar o fundo. O navio flutua ali, virado para onde você olha.",
                "Ande pelos conveses e interiores. Fique num posto e aperte [H] para assumi-lo; aperte [H] de novo para sair. A mesa de cartas abre uma tela: feche-a para sair.",
                "Na 1.1.2, um navio não pode voltar a ser item no modo sobrevivência: o ponto a clicar fica dentro do casco, fora de alcance de fora do convés.",
            ],
            "keys": [
                ["Leme", "[,] e [.] giram o timão; ele fica onde você deixar, e os dois juntos o centralizam. Na 1.1.2, o navio vira ao contrário dos nomes e da indicação do leme: [,] leva a proa para boreste (direita), [.] para bombordo (esquerda)."],
                ["Máquina", "[=] avante; [-] volta em direção a parar. A manete fica onde você deixar. Na 1.1.2, a ré (abaixo de 0) não dá empuxo."],
                ["Manter o rumo", "[;] mantém o rumo que o navio tem quando você aperta, enquanto o timão estiver centralizado."],
                ["Instrumentos", "Aparecem acima da barra rápida enquanto você está no timão."],
            ],
            "lists": [
                ["Mesa de cartas", [
                    "Na mesa de cartas, [H] abre a carta. O clique esquerdo adiciona um ponto de rota; a roda do mouse muda a escala.",
                    "Os botões ligam ou desligam o piloto automático e apagam a rota. Um trecho que cruza terra ou águas rasas é recusado. O piloto automático só governa o leme: ponha a máquina avante no timão; no último ponto ele para a máquina.",
                ]],
                ["Portas (classe Leviathan)", [
                    "Parado (abaixo de 0,3 m/s, máquina em 0) e no timão, ['] abre e fecha a viseira de proa e as rampas.",
                    "A máquina não dá empuxo até as portas fecharem. Dá para andar nas rampas quando estão totalmente abaixadas.",
                ]],
                ["CIC (classe Dreadnought)", [
                    "Artilharia: as duas torres triplas apontam para o ponto que você olha. O clique esquerdo dispara uma salva, a cada 10 segundos; o direito lança o VLS contra o alvo travado pelo radar, depois que a escotilha abre.",
                    "Sonar: navios, barcos, nadadores e contatos submersos numa tela de varredura.",
                ]],
            ],
        },
    },
    "it": {
        "heading": "Comandi",
        "air": {
            "title": "Velivoli: l’aereo di linea Stratos-900 e il caccia Aegis-X",
            "facts": [
                "Posizionare: usa l’oggetto a terra, dove c’è spazio; il velivolo resta lì, rivolto dove guardi.",
                "Salire: clic destro al centro del velivolo. Chi sale per primo pilota (lo Stratos-900 ha 18 posti). Per scendere usa «Accovacciati»; in volo non si può.",
                "Carburante: a terra, usa un ⟨Propellant Canister⟩ sul velivolo, uno per uso.",
                "Recuperare: fermo a terra e senza nessuno a bordo, tieni premuto «Accovacciati» e fai clic destro a mano vuota.",
            ],
            "keys": [
                ["Beccheggio e rollio", "Il mouse (in alto alza il muso, a destra rolla a destra) oppure [↑] [↓] [←] [→]. La barra torna al centro appena il mouse si ferma o rilasci il tasto."],
                ["Manetta", "[W] più, [S] meno. La leva resta dove la lasci."],
                ["Timone", "[A] / [D] (a terra girano anche il ruotino anteriore)."],
                ["Freni delle ruote", "[SPACE]"],
                ["Guardarsi intorno", "Tieni premuto [LALT] (su Mac, [LOPT]); nel frattempo il mouse lascia la barra."],
                ["Flap", "[R], uno scatto per pressione; dopo l’ultimo si ritraggono."],
                ["Carrello", "[U]. Non si ritrae finché le ruote reggono peso."],
                ["Tettuccio / rampa posteriore", "[Y]: il tettuccio dell’Aegis-X, la rampa posteriore dello Stratos-900. Si aprono solo a terra sotto 1 m/s e si richiudono da soli appena il velivolo si muove. La rampa è solo scenica: si sale con il clic destro."],
                ["Gancio d’appontaggio (Aegis-X)", "[K]"],
                ["Postbruciatore / inversione di spinta", "[Z]: sull’Aegis-X, il postbruciatore finché lo tieni premuto; senza, la manetta al massimo dà il 60% della spinta. Sullo Stratos-900 attiva o disattiva l’inversione di spinta, che spinge secondo la manetta, fino al 40%."],
            ],
            "lists": [
                ["Decollo e atterraggio", [
                    "Decollo: flap con [R], manetta al massimo con [W] (sull’Aegis-X tieni premuto anche [Z]); presa velocità, alza il muso col mouse, poi ritrai il carrello con [U].",
                    "Atterraggio: riduci con [S], estrai il carrello con [U] e i flap con [R]. Dopo il contatto, frena con [SPACE]; sullo Stratos-900 premi [Z] e dai manetta con [W] per invertire la spinta, e premi di nuovo [Z] prima del decollo successivo.",
                ]],
                ["Armamento dell’Aegis-X", [
                    "Caricare: usa un ⟨Cherry Guided Missile⟩ su un Aegis-X a terra, uno per uso. Ne porta due, e uno nuovo arriva carico.",
                    "Il radar sorveglia 30° attorno al muso fino a 512 blocchi e aggancia il contatto più vicino al muso dopo averlo tenuto per circa 1,5 secondi. [N] passa tra bersagli aerei e a terra; [M] passa al contatto successivo e l’aggancio ricomincia.",
                    "[J] lancia un missile sul bersaglio agganciato: solo in volo, al massimo uno al secondo.",
                ]],
            ],
        },
        "sea": {
            "title": "Navi: il traghetto classe Leviathan e il cacciatorpediniere classe Dreadnought",
            "facts": [
                "Posizionare: usa l’oggetto sul fondale, sotto acqua profonda almeno quanto il suo pescaggio per tutta la lunghezza (3,5 m la classe Leviathan, 4 m la classe Dreadnought). Il mirino attraversa l’acqua, quindi in acque profonde nuota sopra il punto finché il fondale è a portata. La nave galleggia lì, rivolta dove guardi.",
                "Cammina sui ponti e negli interni. Mettiti a una postazione e premi [H] per occuparla; premi di nuovo [H] per lasciarla. Il tavolo delle carte apre una schermata: chiudila per lasciarlo.",
                "Nella 1.1.2 una nave non può tornare oggetto in sopravvivenza: il punto da cliccare è dentro lo scafo, fuori portata da fuori del ponte.",
            ],
            "keys": [
                ["Timone", "[,] e [.] girano la ruota; resta dove la lasci, ed entrambi insieme la centrano. Nella 1.1.2 la nave vira al contrario dei loro nomi e dell’indicazione del timone: [,] porta la prua a dritta (destra), [.] a sinistra."],
                ["Macchina", "[=] avanti; [-] torna verso l’arresto. La leva resta dove la lasci. Nella 1.1.2, indietro (sotto 0) non dà spinta."],
                ["Mantenimento della rotta", "[;] tiene la rotta che la nave ha quando lo premi, finché la ruota è al centro."],
                ["Strumenti", "Compaiono sopra la barra di scelta rapida mentre sei al timone."],
            ],
            "lists": [
                ["Tavolo delle carte", [
                    "Al tavolo delle carte, [H] apre la carta. Il clic sinistro aggiunge un punto di rotta; la rotellina cambia la scala.",
                    "I suoi pulsanti inseriscono o disinseriscono il pilota automatico e cancellano la rotta. Un tratto che attraversa terra o acque basse viene rifiutato. Il pilota automatico governa solo il timone: metti la macchina avanti al timone; all’ultimo punto la ferma.",
                ]],
                ["Porte (classe Leviathan)", [
                    "Da ferma (sotto 0,3 m/s, macchina a 0) e al timone, ['] apre e chiude il visore di prua e le rampe.",
                    "La macchina non dà spinta finché le porte non sono chiuse. Sulle rampe si cammina quando sono del tutto abbassate.",
                ]],
                ["CIC (classe Dreadnought)", [
                    "Direzione del tiro: le due torri trinate puntano dove guardi. Il clic sinistro spara una salva, ogni 10 secondi; il destro lancia il VLS sul bersaglio agganciato dal radar, una volta aperto il portello.",
                    "Sonar: navi, barche, nuotatori e contatti sommersi su uno schermo a scansione.",
                ]],
            ],
        },
    },
    "ar": {
        "heading": "طريقة التحكم",
        "air": {
            "title": "الطائرات: طائرة الركاب Stratos-900 والمقاتلة Aegis-X",
            "facts": [
                "الوضع: استخدم العنصر على الأرض حيث يتسع لها المكان، فتقف هناك متجهةً إلى حيث تنظر.",
                "الصعود: انقر بالزر الأيمن على منتصف الطائرة. أول من يصعد هو الطيار (في Stratos-900 ثمانية عشر مقعدًا). للنزول استخدم «التسلل»، ولا يمكن النزول في الجو.",
                "الوقود: على الأرض، استخدم ⟨Propellant Canister⟩ على الطائرة، واحدًا في كل مرة.",
                "الاسترداد: والطائرة متوقفة على الأرض ولا أحد على متنها، اضغط «التسلل» مطوّلًا وانقر بالزر الأيمن بيد فارغة.",
            ],
            "keys": [
                ["الانحدار والدوران", "الفأرة (إلى الأعلى ترفع المقدّمة، وإلى اليمين تدور يمينًا) أو [↑] [↓] [←] [→]. يعود عمود التحكم إلى المنتصف بمجرد توقف الفأرة أو ترك المفتاح."],
                ["قوة الدفع", "[W] زيادة، [S] إنقاص. تبقى الذراع حيث تتركها."],
                ["الدفّة", "[A] / [D] (وعلى الأرض تديران العجلة الأمامية أيضًا)."],
                ["مكابح العجلات", "[SPACE]"],
                ["النظر حولك", "اضغط [LALT] مطوّلًا (على Mac: [LOPT])، وفي أثناء ذلك لا تحرّك الفأرة عمود التحكم."],
                ["القلابات", "[R]، درجة واحدة لكل ضغطة، وبعد الأخيرة تُرفع."],
                ["عجلات الهبوط", "[U]. لا تُطوى ما دامت العجلات تحمل وزنًا."],
                ["غطاء قمرة القيادة / المنحدر الخلفي", "[Y]: غطاء القمرة في Aegis-X، والمنحدر الخلفي في Stratos-900. لا يُفتحان إلا على الأرض بسرعة أقل من 1 م/ث، ويُغلقان من تلقاء نفسيهما حين تتحرك الطائرة. المنحدر للمظهر فقط: اصعد بالنقر الأيمن."],
                ["خطّاف الهبوط (Aegis-X)", "[K]"],
                ["الحارق اللاحق / عكس الدفع", "[Z]: في Aegis-X الحارق اللاحق ما دمت تضغطه، ومن دونه لا يعطي الدفع الكامل إلا 60%. وفي Stratos-900 يشغّل عكس الدفع أو يوقفه، ويدفع إلى الخلف بحسب الذراع حتى 40%."],
            ],
            "lists": [
                ["الإقلاع والهبوط", [
                    "الإقلاع: القلابات بـ[R]، والدفع الكامل بـ[W] (وفي Aegis-X اضغط [Z] أيضًا)، وحين تكتسب السرعة ارفع المقدّمة بالفأرة، ثم اطوِ العجلات بـ[U].",
                    "الهبوط: خفّف الدفع بـ[S]، وأنزل العجلات بـ[U] والقلابات بـ[R]. بعد ملامسة الأرض فرمل بـ[SPACE]؛ وفي Stratos-900 اضغط [Z] ثم زِد الدفع بـ[W] لعكس الدفع، واضغط [Z] مرة أخرى قبل الإقلاع التالي.",
                ]],
                ["تسليح Aegis-X", [
                    "التحميل: استخدم ⟨Cherry Guided Missile⟩ على Aegis-X وهي على الأرض، صاروخًا في كل مرة. تحمل صاروخين، والطائرة الجديدة تأتي محمّلة.",
                    "يراقب الرادار 30° حول المقدّمة حتى 512 كتلة، ويقفل على أقرب هدف إلى المقدّمة بعد أن يبقيه نحو 1.5 ثانية. [N] يبدّل بين أهداف الجو والأرض، و[M] ينتقل إلى الهدف التالي ويبدأ القفل من جديد.",
                    "[J] يطلق صاروخًا على الهدف المقفل: في الجو فقط، وصاروخًا واحدًا في الثانية على الأكثر.",
                ]],
            ],
        },
        "sea": {
            "title": "السفن: العبّارة من فئة Leviathan والمدمّرة من فئة Dreadnought",
            "facts": [
                "الوضع: استخدم العنصر على القاع، تحت ماء لا يقل عمقه عن غاطسها على طول بدنها كله (3.5 م لفئة Leviathan و4 م لفئة Dreadnought). مؤشر التصويب يمر عبر الماء، فاسبح في المياه العميقة فوق الموضع حتى يصبح القاع في متناولك. تطفو السفينة هناك متجهةً إلى حيث تنظر.",
                "تجوّل على أسطحها وفي داخلها. قف عند موقع عمل واضغط [H] لتتولاه، واضغط [H] مجددًا لتتركه. طاولة الخرائط تفتح شاشة: أغلقها لتتركها.",
                "في 1.1.2 لا يمكن إعادة السفينة إلى عنصر في وضع البقاء: الموضع الذي يجب النقر عليه داخل البدن، بعيدًا عن المتناول من خارج السطح.",
            ],
            "keys": [
                ["الدفّة", "[,] و[.] يديران عجلة القيادة، وتبقى حيث تتركها، والضغط على الاثنين معًا يعيدها إلى المنتصف. في 1.1.2 تدور السفينة عكس اسميهما وعكس ما يعرضه مؤشر الدفّة: [,] يدير المقدّمة إلى الميمنة (اليمين)، و[.] إلى الميسرة (اليسار)."],
                ["المحرّك", "[=] إلى الأمام؛ [-] يعيد الذراع نحو التوقف. تبقى الذراع حيث تتركها. في 1.1.2 لا يعطي الرجوع إلى الخلف (أقل من 0) أي دفع."],
                ["تثبيت الاتجاه", "[;] يثبّت الاتجاه الذي تكون عليه لحظة الضغط، ما دامت عجلة القيادة في المنتصف."],
                ["العدّادات", "تظهر فوق شريط المهام ما دمت عند عجلة القيادة."],
            ],
            "lists": [
                ["طاولة الخرائط", [
                    "عند طاولة الخرائط يفتح [H] الخريطة. النقر الأيسر يضيف نقطة مسار، وعجلة الفأرة تغيّر المقياس.",
                    "أزرارها تشغّل الملاحة الآلية أو توقفها وتمسح المسار. يُرفض أي مقطع يعبر اليابسة أو المياه الضحلة. الملاحة الآلية تتولى الدفّة فقط: اجعل المحرّك إلى الأمام من عجلة القيادة، وهي توقفه عند آخر نقطة.",
                ]],
                ["الأبواب (فئة Leviathan)", [
                    "والسفينة متوقفة (أقل من 0.3 م/ث والمحرّك على 0) وأنت عند عجلة القيادة، يفتح ['] واقي المقدّمة والمنحدرات ويغلقها.",
                    "لا يعطي المحرّك دفعًا حتى تُغلق الأبواب. ويمكن المشي على المنحدرات حين تنزل تمامًا.",
                ]],
                ["مركز المعلومات القتالية (فئة Dreadnought)", [
                    "موقع المدفعية: يتجه البرجان الثلاثيان إلى النقطة التي تنظر إليها. النقر الأيسر يطلق رشقة كل 10 ثوانٍ، والنقر الأيمن يطلق منظومة الإطلاق العمودي على الهدف الذي أقفل عليه الرادار بعد انفتاح فتحتها.",
                    "السونار: السفن والقوارب والسبّاحون والأهداف المغمورة على شاشة مسح دوّارة.",
                ]],
            ],
        },
    },
    "ru": {
        "heading": "Управление",
        "air": {
            "title": "Самолёты: авиалайнер Stratos-900 и истребитель Aegis-X",
            "facts": [
                "Установка: используйте предмет на земле, где ему хватает места, — самолёт встанет там носом туда, куда вы смотрите.",
                "Посадка: правый клик по середине самолёта. Первый севший — пилот (в Stratos-900 18 мест). Выйти — «Красться»; в воздухе выйти нельзя.",
                "Топливо: на земле используйте на самолёте ⟨Propellant Canister⟩, по одной за раз.",
                "Возврат в предмет: когда самолёт стоит на земле и на борту никого нет, удерживайте «Красться» и сделайте правый клик пустой рукой.",
            ],
            "keys": [
                ["Тангаж и крен", "Мышь (вверх — нос вверх, вправо — крен вправо) или [↑] [↓] [←] [→]. Ручка возвращается в центр, как только мышь останавливается или клавиша отпущена."],
                ["Тяга", "[W] больше, [S] меньше. Рычаг остаётся там, где вы его оставили."],
                ["Руль направления", "[A] / [D] (на земле они также поворачивают носовое колесо)."],
                ["Тормоза колёс", "[SPACE]"],
                ["Осмотреться", "Удерживайте [LALT] (на Mac — [LOPT]); в это время мышь не двигает ручку."],
                ["Закрылки", "[R], одна ступень за нажатие; после последней — убраны."],
                ["Шасси", "[U]. Не убирается, пока колёса несут вес."],
                ["Фонарь / задняя рампа", "[Y]: фонарь Aegis-X, задняя рампа Stratos-900. Открываются только на земле при скорости меньше 1 м/с и сами закрываются, когда самолёт трогается. Рампа — только для вида: садятся правым кликом."],
                ["Посадочный гак (Aegis-X)", "[K]"],
                ["Форсаж / реверс", "[Z]: на Aegis-X — форсаж, пока клавиша нажата; без него полная тяга даёт лишь 60 %. На Stratos-900 — включить или выключить реверс, который тянет назад по рычагу, до 40 %."],
            ],
            "lists": [
                ["Взлёт и посадка", [
                    "Взлёт: закрылки — [R], полная тяга — [W] (на Aegis-X держите ещё и [Z]); набрав скорость, поднимите нос мышью, затем уберите шасси — [U].",
                    "Посадка: сбросьте тягу — [S], выпустите шасси — [U] и закрылки — [R]. После касания тормозите — [SPACE]; на Stratos-900 нажмите [Z] и добавьте тягу — [W], чтобы включить реверс, а перед следующим взлётом снова нажмите [Z].",
                ]],
                ["Вооружение Aegis-X", [
                    "Зарядка: используйте ⟨Cherry Guided Missile⟩ на Aegis-X, стоящем на земле, — по одной ракете. Он несёт две, и новый самолёт появляется заряженным.",
                    "Радар смотрит в пределах 30° вокруг носа до 512 блоков и захватывает ближайшую к носу цель, удержанную около 1,5 секунды. [N] переключает воздушные и наземные цели, [M] переходит к следующей цели, и захват начинается заново.",
                    "[J] пускает ракету по захваченной цели: только в воздухе, не чаще одной в секунду.",
                ]],
            ],
        },
        "sea": {
            "title": "Корабли: паром класса Leviathan и эсминец класса Dreadnought",
            "facts": [
                "Установка: используйте предмет на дне под водой не мельче его осадки по всей длине (3,5 м у класса Leviathan, 4 м у класса Dreadnought). Прицел проходит сквозь воду, поэтому на глубине плывите над этим местом, пока дно не окажется в пределах досягаемости. Корабль всплывёт там носом туда, куда вы смотрите.",
                "По палубам и внутренним помещениям можно ходить. Встаньте у поста и нажмите [H], чтобы занять его; нажмите [H] снова, чтобы уйти. Штурманский стол открывает экран: закройте его, чтобы уйти.",
                "В 1.1.2 корабль нельзя вернуть в предмет в режиме выживания: место для клика находится внутри корпуса и недосягаемо снаружи палубы.",
            ],
            "keys": [
                ["Руль", "[,] и [.] вращают штурвал; он остаётся там, где вы его оставили, а обе клавиши вместе ставят его прямо. В 1.1.2 корабль поворачивает наоборот их названиям и показаниям руля: [,] уводит нос вправо (на правый борт), [.] — влево."],
                ["Машина", "[=] вперёд; [-] обратно к «стоп». Рычаг остаётся там, где вы его оставили. В 1.1.2 задний ход (ниже 0) тяги не даёт."],
                ["Удержание курса", "[;] держит курс, который был при нажатии, пока штурвал стоит прямо."],
                ["Приборы", "Показаны над панелью быстрого доступа, пока вы у штурвала."],
            ],
            "lists": [
                ["Штурманский стол", [
                    "У штурманского стола [H] открывает карту. Левый клик добавляет путевую точку, колесо мыши меняет масштаб.",
                    "Кнопки включают и выключают автопилот и стирают маршрут. Участок через сушу или мелководье отклоняется. Автопилот только рулит: дайте ход вперёд у штурвала; в последней точке он останавливает машину.",
                ]],
                ["Ворота (класс Leviathan)", [
                    "На стопе (меньше 0,3 м/с, машина на 0) и у штурвала ['] открывает и закрывает носовой визор и рампы.",
                    "Пока ворота не закрыты, машина не даёт тяги. По рампам можно ходить, когда они опущены полностью.",
                ]],
                ["БИЦ (класс Dreadnought)", [
                    "Пост артиллериста: обе трёхорудийные башни наводятся на точку, куда вы смотрите. Левый клик — залп, раз в 10 секунд; правый клик — пуск УВП по цели, захваченной радаром, после открытия крышки.",
                    "Сонар: корабли, лодки, пловцы и подводные контакты на экране кругового обзора.",
                ]],
            ],
        },
    },
    "id": {
        "heading": "Kontrol",
        "air": {
            "title": "Pesawat: pesawat penumpang Stratos-900 dan jet tempur Aegis-X",
            "facts": [
                "Menaruh: gunakan itemnya di tanah yang cukup lapang; pesawat berdiri di sana menghadap ke arah pandanganmu.",
                "Naik: klik kanan bagian tengah pesawat. Yang naik pertama menjadi pilot (Stratos-900 punya 18 kursi). Turun dengan “Jongkok”; tidak bisa turun di udara.",
                "Bahan bakar: di darat, gunakan ⟨Propellant Canister⟩ pada pesawat, satu per penggunaan.",
                "Mengambil kembali: saat diam di darat dan tak ada yang naik, tahan “Jongkok” lalu klik kanan dengan tangan kosong.",
            ],
            "keys": [
                ["Angguk dan guling", "Mouse (ke atas mengangkat hidung, ke kanan berguling ke kanan) atau [↑] [↓] [←] [→]. Tongkat kembali ke tengah begitu mouse berhenti atau tombol dilepas."],
                ["Daya dorong", "[W] tambah, [S] kurangi. Tuasnya tetap di posisi terakhir."],
                ["Kemudi arah", "[A] / [D] (di darat juga membelokkan roda depan)."],
                ["Rem roda", "[SPACE]"],
                ["Melihat sekitar", "Tahan [LALT] (di Mac, [LOPT]); selama itu mouse tidak menggerakkan tongkat."],
                ["Flap", "[R], satu tingkat tiap tekan; setelah yang terakhir, naik kembali."],
                ["Roda pendarat", "[U]. Tidak terlipat selama roda menahan beban."],
                ["Kanopi / ramp belakang", "[Y]: kanopi Aegis-X, ramp belakang Stratos-900. Hanya terbuka di darat di bawah 1 m/s dan menutup sendiri begitu pesawat bergerak. Ramp itu hanya tampilan: naiklah dengan klik kanan."],
                ["Kait pendaratan (Aegis-X)", "[K]"],
                ["Afterburner / dorong balik", "[Z]: pada Aegis-X, afterburner selama ditahan; tanpa itu, daya penuh hanya memberi 60%. Pada Stratos-900, menyalakan atau mematikan dorong balik, yang mendorong sesuai tuas, sampai 40%."],
            ],
            "lists": [
                ["Lepas landas dan mendarat", [
                    "Lepas landas: flap dengan [R], daya penuh dengan [W] (pada Aegis-X, tahan juga [Z]); setelah cukup cepat, angkat hidung dengan mouse, lalu lipat roda dengan [U].",
                    "Mendarat: kurangi daya dengan [S], turunkan roda dengan [U] dan flap dengan [R]. Setelah menyentuh landasan, rem dengan [SPACE]; pada Stratos-900, tekan [Z] lalu tambah daya dengan [W] untuk dorong balik, dan tekan [Z] lagi sebelum lepas landas berikutnya.",
                ]],
                ["Persenjataan Aegis-X", [
                    "Mengisi: gunakan ⟨Cherry Guided Missile⟩ pada Aegis-X di darat, satu per penggunaan. Ia membawa dua, dan yang baru datang sudah terisi.",
                    "Radar mengawasi 30° di sekitar hidung sejauh 512 blok dan mengunci kontak yang paling dekat dengan hidung setelah menahannya sekitar 1,5 detik. [N] beralih antara sasaran udara dan darat; [M] pindah ke kontak berikutnya, dan penguncian dimulai lagi.",
                    "[J] menembakkan rudal ke sasaran yang terkunci: hanya di udara, paling banyak satu per detik.",
                ]],
            ],
        },
        "sea": {
            "title": "Kapal: feri kelas Leviathan dan kapal perusak kelas Dreadnought",
            "facts": [
                "Menaruh: gunakan itemnya pada dasar di bawah air yang setidaknya sedalam sarat airnya di sepanjang lambung (3,5 m untuk kelas Leviathan, 4 m untuk kelas Dreadnought). Bidikan menembus air, jadi di air dalam berenanglah di atas tempat itu sampai dasarnya terjangkau. Kapal mengapung di sana menghadap arah pandanganmu.",
                "Jelajahi dek dan bagian dalamnya. Berdirilah di sebuah pos dan tekan [H] untuk mengambilnya; tekan [H] lagi untuk pergi. Meja peta membuka layar: tutup layarnya untuk pergi.",
                "Di 1.1.2, kapal tidak bisa dijadikan item lagi dalam mode bertahan hidup: titik yang harus diklik ada di dalam lambung, di luar jangkauan dari luar dek.",
            ],
            "keys": [
                ["Kemudi", "[,] dan [.] memutar roda kemudi; roda tetap di posisi terakhir, dan keduanya bersamaan mengembalikannya ke tengah. Di 1.1.2, kapal berbelok berlawanan dengan nama tombol dan tampilan kemudi: [,] membelokkan haluan ke kanan (starboard), [.] ke kiri (port)."],
                ["Mesin", "[=] maju; [-] kembali ke arah berhenti. Tuasnya tetap di posisi terakhir. Di 1.1.2, mundur (di bawah 0) tidak memberi daya dorong."],
                ["Tahan haluan", "[;] menahan haluan saat tombol ditekan, selama roda kemudi di tengah."],
                ["Instrumen", "Tampil di atas bilah benda selama kamu memegang kemudi."],
            ],
            "lists": [
                ["Meja peta", [
                    "Di meja peta, [H] membuka peta. Klik kiri menambah titik rute; roda mouse mengubah skala.",
                    "Tombolnya menyalakan atau mematikan autopilot dan menghapus rute. Ruas yang melintasi daratan atau perairan dangkal ditolak. Autopilot hanya mengemudi: majukan mesin di roda kemudi; di titik terakhir ia menghentikan mesin.",
                ]],
                ["Pintu (kelas Leviathan)", [
                    "Saat diam (di bawah 0,3 m/s, mesin 0) dan memegang kemudi, ['] membuka dan menutup visor haluan dan ramp.",
                    "Mesin tidak memberi daya dorong sampai pintu tertutup. Ramp bisa diinjak setelah turun sepenuhnya.",
                ]],
                ["CIC (kelas Dreadnought)", [
                    "Penembak: kedua turet berlaras tiga membidik titik yang kamu lihat. Klik kiri menembakkan satu salvo, tiap 10 detik; klik kanan meluncurkan VLS ke sasaran yang dikunci radar, setelah palkanya terbuka.",
                    "Sonar: kapal, perahu, perenang, dan kontak di bawah air pada layar pindai berputar.",
                ]],
            ],
        },
    },
    "de": {
        "heading": "Steuerung",
        "air": {
            "title": "Flugzeuge: das Verkehrsflugzeug Stratos-900 und der Jäger Aegis-X",
            "facts": [
                "Aufstellen: Benutze den Gegenstand auf dem Boden, wo genug Platz ist; das Flugzeug steht dann dort, mit der Nase in Blickrichtung.",
                "Einsteigen: Rechtsklick auf die Mitte des Flugzeugs. Wer zuerst einsteigt, fliegt (die Stratos-900 hat 18 Sitze). Aussteigen mit „Schleichen“; in der Luft geht das nicht.",
                "Treibstoff: Benutze am Boden einen ⟨Propellant Canister⟩ am Flugzeug, einen pro Benutzung.",
                "Einsammeln: Steht es am Boden still und ist niemand an Bord, halte „Schleichen“ und mache mit leerer Hand einen Rechtsklick.",
            ],
            "keys": [
                ["Nicken und Rollen", "Die Maus (nach oben hebt die Nase, nach rechts rollt nach rechts) oder [↑] [↓] [←] [→]. Der Knüppel geht zur Mitte zurück, sobald die Maus stillsteht oder die Taste losgelassen wird."],
                ["Schub", "[W] mehr, [S] weniger. Der Hebel bleibt, wo du ihn lässt."],
                ["Seitenruder", "[A] / [D] (am Boden lenken sie auch das Bugrad)."],
                ["Radbremsen", "[SPACE]"],
                ["Umsehen", "[LALT] gedrückt halten (auf dem Mac [LOPT]); solange bewegt die Maus nicht den Knüppel."],
                ["Landeklappen", "[R], eine Stufe pro Druck; nach der letzten wieder eingefahren."],
                ["Fahrwerk", "[U]. Es fährt nicht ein, solange die Räder Last tragen."],
                ["Kabinenhaube / Heckrampe", "[Y]: die Haube der Aegis-X, die Heckrampe der Stratos-900. Sie öffnen sich nur am Boden unter 1 m/s und schließen sich von selbst, sobald das Flugzeug anrollt. Die Rampe ist nur Optik: eingestiegen wird per Rechtsklick."],
                ["Fanghaken (Aegis-X)", "[K]"],
                ["Nachbrenner / Schubumkehr", "[Z]: bei der Aegis-X der Nachbrenner, solange gedrückt; ohne ihn gibt Vollschub nur 60 %. Bei der Stratos-900 Schubumkehr an oder aus; sie schiebt je nach Hebel, bis 40 %."],
            ],
            "lists": [
                ["Start und Landung", [
                    "Start: Klappen mit [R], Vollschub mit [W] (bei der Aegis-X zusätzlich [Z] halten); mit genug Fahrt die Nase mit der Maus heben, dann das Fahrwerk mit [U] einfahren.",
                    "Landung: Schub mit [S] zurücknehmen, Fahrwerk mit [U] und Klappen mit [R] ausfahren. Nach dem Aufsetzen mit [SPACE] bremsen; bei der Stratos-900 für Schubumkehr [Z] drücken und mit [W] Schub geben, und vor dem nächsten Start [Z] erneut drücken.",
                ]],
                ["Bewaffnung der Aegis-X", [
                    "Laden: Benutze eine ⟨Cherry Guided Missile⟩ an einer Aegis-X am Boden, eine pro Benutzung. Sie trägt zwei, und eine neue kommt geladen.",
                    "Das Radar überwacht 30° um die Nase bis 512 Blöcke und schaltet den Kontakt, der der Nase am nächsten ist, auf, nachdem es ihn etwa 1,5 Sekunden gehalten hat. [N] wechselt zwischen Luft- und Bodenzielen; [M] geht zum nächsten Kontakt, und die Aufschaltung beginnt neu.",
                    "[J] feuert eine Rakete auf das aufgeschaltete Ziel: nur in der Luft, höchstens eine pro Sekunde.",
                ]],
            ],
        },
        "sea": {
            "title": "Schiffe: die Fähre der Leviathan-Klasse und der Zerstörer der Dreadnought-Klasse",
            "facts": [
                "Aufstellen: Benutze den Gegenstand auf dem Grund, unter Wasser, das über die ganze Länge mindestens so tief ist wie der Tiefgang (3,5 m bei der Leviathan-Klasse, 4 m bei der Dreadnought-Klasse). Das Fadenkreuz geht durch Wasser hindurch; schwimm in tiefem Wasser über die Stelle, bis der Grund in Reichweite ist. Das Schiff schwimmt dann dort, mit dem Bug in Blickrichtung.",
                "Du kannst über die Decks und durch die Innenräume gehen. Stell dich an eine Station und drücke [H], um sie zu übernehmen; drücke [H] erneut, um sie zu verlassen. Der Kartentisch öffnet einen Bildschirm: schließe ihn, um ihn zu verlassen.",
                "In 1.1.2 lässt sich ein Schiff im Überlebensmodus nicht wieder zum Gegenstand machen: Die Stelle zum Anklicken liegt im Rumpf, außer Reichweite von außerhalb des Decks.",
            ],
            "keys": [
                ["Ruder", "[,] und [.] drehen das Steuerrad; es bleibt, wo du es lässt, und beide zusammen stellen es mittschiffs. In 1.1.2 dreht das Schiff entgegen ihren Namen und der Ruderanzeige: [,] dreht den Bug nach Steuerbord (rechts), [.] nach Backbord (links)."],
                ["Maschine", "[=] voraus; [-] zurück Richtung Stopp. Der Hebel bleibt, wo du ihn lässt. In 1.1.2 gibt Zurück (unter 0) keinen Schub."],
                ["Kurs halten", "[;] hält den Kurs, den das Schiff beim Drücken hat, solange das Rad mittschiffs steht."],
                ["Instrumente", "Werden über der Schnellzugriffsleiste angezeigt, solange du am Ruder stehst."],
            ],
            "lists": [
                ["Kartentisch", [
                    "Am Kartentisch öffnet [H] die Seekarte. Linksklick fügt einen Wegpunkt hinzu; das Mausrad ändert den Maßstab.",
                    "Seine Knöpfe schalten den Autopiloten ein oder aus und löschen die Route. Ein Abschnitt über Land oder Flachwasser wird abgelehnt. Der Autopilot steuert nur: stelle die Maschine am Ruder auf voraus; am letzten Wegpunkt stoppt er sie.",
                ]],
                ["Tore (Leviathan-Klasse)", [
                    "Im Stillstand (unter 0,3 m/s, Maschine auf 0) und am Ruder öffnet und schließt ['] das Bugvisier und die Rampen.",
                    "Die Maschine gibt keinen Schub, bis die Tore geschlossen sind. Die Rampen sind begehbar, sobald sie ganz unten sind.",
                ]],
                ["Operationszentrale (Dreadnought-Klasse)", [
                    "Geschützstation: Beide Drillingstürme richten sich auf den Punkt, den du ansiehst. Linksklick feuert eine Salve, alle 10 Sekunden; Rechtsklick startet das VLS auf das vom Radar aufgeschaltete Ziel, sobald seine Klappe offen ist.",
                    "Sonar: Schiffe, Boote, Schwimmer und getauchte Kontakte auf einem umlaufenden Suchschirm.",
                ]],
            ],
        },
    },
    "tr": {
        "heading": "Kontroller",
        "air": {
            "title": "Uçaklar: yolcu uçağı Stratos-900 ve savaş uçağı Aegis-X",
            "facts": [
                "Yerleştirme: eşyayı yeterince yer olan bir zeminde kullanın; uçak orada, baktığınız yöne burnunu çevirip durur.",
                "Binme: uçağın ortasına sağ tıklayın. İlk binen pilottur (Stratos-900’de 18 koltuk var). İnmek için “Eğilme”; havadayken inilemez.",
                "Yakıt: yerdeyken uçağa bir ⟨Propellant Canister⟩ kullanın; her kullanımda bir tane.",
                "Geri alma: uçak yerde dururken ve kimse binmemişken “Eğilme”yi basılı tutup boş elle sağ tıklayın.",
            ],
            "keys": [
                ["Yunuslama ve yatış", "Fare (yukarı burnu kaldırır, sağa sağa yatırır) ya da [↑] [↓] [←] [→]. Fare durduğu ya da tuş bırakıldığı anda lövye ortaya döner."],
                ["İtki", "[W] artır, [S] azalt. Kol bıraktığınız yerde kalır."],
                ["İstikamet dümeni", "[A] / [D] (yerde burun tekerini de çevirir)."],
                ["Tekerlek frenleri", "[SPACE]"],
                ["Etrafa bakma", "[LALT] basılıyken (Mac’te [LOPT]); bu sırada fare lövyeyi hareket ettirmez."],
                ["Flaplar", "[R], her basışta bir kademe; sonuncudan sonra toplanır."],
                ["İniş takımı", "[U]. Tekerlekler yük taşırken toplanmaz."],
                ["Kanopi / arka rampa", "[Y]: Aegis-X’in kanopisi, Stratos-900’ün arka rampası. Yalnızca yerde 1 m/s’nin altında açılır ve uçak hareket edince kendiliğinden kapanır. Rampa yalnızca görünüş içindir: binmek için sağ tıklayın."],
                ["Kuyruk kancası (Aegis-X)", "[K]"],
                ["Art yakıcı / ters itki", "[Z]: Aegis-X’te basılı tutulduğu sürece art yakıcı; o olmadan tam itki yalnızca %60 verir. Stratos-900’de ters itkiyi açar ya da kapatır; ters itki kola göre, en fazla %40 iter."],
            ],
            "lists": [
                ["Kalkış ve iniş", [
                    "Kalkış: [R] ile flaplar, [W] ile tam itki (Aegis-X’te [Z]’yi de basılı tutun); hızlanınca fareyle burnu kaldırın, ardından [U] ile iniş takımını toplayın.",
                    "İniş: [S] ile itkiyi azaltın, [U] ile iniş takımını, [R] ile flapları indirin. Teker koyduktan sonra [SPACE] ile frenleyin; Stratos-900’de ters itki için [Z]’ye basıp [W] ile itki verin ve bir sonraki kalkıştan önce [Z]’ye yeniden basın.",
                ]],
                ["Aegis-X silahları", [
                    "Yükleme: yerdeki bir Aegis-X’e ⟨Cherry Guided Missile⟩ kullanın; her kullanımda bir füze. İki füze taşır ve yeni uçak dolu gelir.",
                    "Radar, burnun çevresindeki 30° içini 512 bloğa kadar izler ve burna en yakın teması yaklaşık 1,5 saniye tuttuktan sonra kilitler. [N] hava ve kara hedefleri arasında geçiş yapar; [M] sonraki temasa geçer ve kilitleme yeniden başlar.",
                    "[J] kilitli hedefe füze ateşler: yalnızca havadayken, saniyede en fazla bir tane.",
                ]],
            ],
        },
        "sea": {
            "title": "Gemiler: Leviathan sınıfı feribot ve Dreadnought sınıfı muhrip",
            "facts": [
                "Yerleştirme: eşyayı, boyu boyunca en az su çekimi kadar derin suyun (Leviathan sınıfı 3,5 m, Dreadnought sınıfı 4 m) altındaki zeminde kullanın. Nişangâh suyun içinden geçer; derin suda zemine uzanabilene kadar o noktanın üstünde yüzün. Gemi orada, baktığınız yöne pruvasını çevirip yüzer.",
                "Güvertelerinde ve iç mekânlarında yürüyebilirsiniz. Bir görev yerinde durup [H] tuşuna basarak görevi alın; ayrılmak için [H] tuşuna yeniden basın. Harita masası bir ekran açar: ayrılmak için ekranı kapatın.",
                "1.1.2’de gemi hayatta kalma modunda yeniden eşyaya dönüştürülemez: tıklanması gereken yer gövdenin içindedir ve güverte dışından erişilemez.",
            ],
            "keys": [
                ["Dümen", "[,] ve [.] dümen dolabını çevirir; dolap bıraktığınız yerde kalır, ikisine birlikte basmak ortalar. 1.1.2’de gemi, tuşların adlarının ve dümen göstergesinin tersine döner: [,] pruvayı sancağa (sağa), [.] iskeleye (sola) çevirir."],
                ["Makine", "[=] ileri; [-] durmaya doğru geri alır. Kol bıraktığınız yerde kalır. 1.1.2’de tornistan (0’ın altı) itki vermez."],
                ["Rota tutma", "[;] basıldığı andaki rotayı, dümen dolabı ortadayken korur."],
                ["Göstergeler", "Dümendeyken araç çubuğunun üstünde görünür."],
            ],
            "lists": [
                ["Harita masası", [
                    "Harita masasında [H] haritayı açar. Sol tık rota noktası ekler; fare tekerleği ölçeği değiştirir.",
                    "Düğmeleri otomatik seyri açar ya da kapatır ve rotayı siler. Karayı ya da sığ suyu geçen bir ayak reddedilir. Otomatik seyir yalnızca dümeni kullanır: makineyi dümende ileriye alın; son noktada makineyi durdurur.",
                ]],
                ["Kapılar (Leviathan sınıfı)", [
                    "Dururken (0,3 m/s altında, makine 0) ve dümendeyken ['] pruva vizörünü ve rampaları açıp kapatır.",
                    "Kapılar kapanana kadar makine itki vermez. Rampalar tamamen indiğinde üzerlerinde yürünebilir.",
                ]],
                ["Muharebe Bilgi Merkezi (Dreadnought sınıfı)", [
                    "Topçu görev yeri: iki üçlü top kulesi baktığınız noktaya döner. Sol tık 10 saniyede bir yaylım ateşi açar; sağ tık, kapağı açıldıktan sonra dikey atış sistemini radarın kilitlendiği hedefe ateşler.",
                    "Sonar: gemiler, tekneler, yüzücüler ve su altındaki temaslar, dönen bir tarama ekranında.",
                ]],
            ],
        },
    },
}

# The page around the cards: its title, its description, and the two notes above the cards.
# {movement}, {flight}, {helm}, {path} and {keybinds} are filled per language (MOVEMENT,
# CATEGORIES, PATH); the Japanese note adds the two JIS keys that differ (see the docstring).
INTRO = {
    "en": {
        "title": "Cherry controls",
        "desc": "How to fly the Stratos-900 and the Aegis-X and sail the Leviathan-Class and the Dreadnought-Class: the default keys and what they do.",
        "note": "These are the default keys of {release}. [W] [A] [S] [D] and [SPACE] are the game’s own “{movement}” keys; the rest are under “{flight}” and “{helm}”. Change any of them in {path}.",
        "layout": "Keys are named by where they sit on a US keyboard. Yours may label the same key differently; {keybinds} shows each one by your keyboard’s name for it.",
    },
    "ja": {
        "title": "Cherry の操作方法",
        "desc": "Stratos-900 と Aegis-X の飛ばし方、Leviathan級と Dreadnought級の動かし方。既定のキーと、その働き。",
        "note": "{release} の既定のキーです。[W] [A] [S] [D] と [SPACE] はゲーム本来の「{movement}」のキー、ほかは「{flight}」と「{helm}」にあります。どれも {path} で変えられます。",
        "layout": "キーは US 配列での位置で書いています。日本語(JIS)キーボードでは [=] が [^] のキー、['] が [:] のキーです。{keybinds}の画面には、お使いのキーボードでの名前で出ます。",
    },
    "es": {
        "title": "Controles de Cherry",
        "desc": "Cómo pilotar el Stratos-900 y el Aegis-X y gobernar los buques clase Leviathan y Dreadnought: las teclas predeterminadas y lo que hacen.",
        "note": "Estas son las teclas predeterminadas de {release}. [W] [A] [S] [D] y [SPACE] son las teclas de «{movement}» del propio juego; las demás están en «{flight}» y «{helm}». Puedes cambiarlas todas en {path}.",
        "layout": "Las teclas se nombran por su posición en un teclado estadounidense. El tuyo puede rotular la misma tecla de otra forma; «{keybinds}» muestra cada una con el nombre que le da tu teclado.",
    },
    "fr": {
        "title": "Commandes de Cherry",
        "desc": "Piloter le Stratos-900 et l’Aegis-X, conduire les navires classe Leviathan et Dreadnought : les touches par défaut et leur rôle.",
        "note": "Ce sont les touches par défaut de {release}. [W] [A] [S] [D] et [SPACE] sont les touches « {movement} » du jeu lui-même ; les autres se trouvent sous « {flight} » et « {helm} ». Toutes se modifient dans {path}.",
        "layout": "Les touches sont désignées par leur place sur un clavier américain (QWERTY) : sur un clavier AZERTY, par exemple, [W] [A] [S] [D] sont [Z] [Q] [S] [D]. « {keybinds} » affiche chaque touche sous le nom que lui donne votre clavier.",
    },
    "zh": {
        "title": "Cherry 操作方法",
        "desc": "驾驶 Stratos-900 与 Aegis-X，操纵 Leviathan 级与 Dreadnought 级舰船：默认按键及其作用。",
        "note": "以下为 {release} 的默认按键。[W] [A] [S] [D] 与 [SPACE] 是游戏自身“{movement}”类的按键，其余位于“{flight}”和“{helm}”中。均可在{path}中修改。",
        "layout": "按键以其在美式键盘上的位置命名。你的键盘可能给同一个键标注不同的名称；“{keybinds}”会以你的键盘所用的名称显示每个键。",
    },
    "ko": {
        "title": "Cherry 조작 방법",
        "desc": "Stratos-900과 Aegis-X를 조종하고 Leviathan급과 Dreadnought급을 운항하는 법: 기본 키와 그 기능.",
        "note": "{release}의 기본 키입니다. [W] [A] [S] [D]와 [SPACE]는 게임 자체의 “{movement}” 키이고, 나머지는 “{flight}”와 “{helm}”에 있습니다. 모두 {path}에서 바꿀 수 있습니다.",
        "layout": "키 이름은 미국식 키보드에서의 위치를 기준으로 적었습니다. 사용하는 키보드에서는 같은 키가 다르게 표시될 수 있으며, “{keybinds}” 화면에는 그 키보드에서의 이름으로 나옵니다.",
    },
    "pt-br": {
        "title": "Controles do Cherry",
        "desc": "Como pilotar o Stratos-900 e o Aegis-X e comandar os navios classe Leviathan e Dreadnought: as teclas padrão e o que fazem.",
        "note": "Estas são as teclas padrão do {release}. [W] [A] [S] [D] e [SPACE] são as teclas de “{movement}” do próprio jogo; as demais ficam em “{flight}” e “{helm}”. Todas podem ser alteradas em {path}.",
        "layout": "As teclas são indicadas pela posição num teclado americano. O seu pode marcar a mesma tecla de outro jeito; “{keybinds}” mostra cada uma com o nome que o seu teclado dá a ela.",
    },
    "it": {
        "title": "Comandi di Cherry",
        "desc": "Come pilotare lo Stratos-900 e l’Aegis-X e condurre le navi classe Leviathan e Dreadnought: i tasti predefiniti e cosa fanno.",
        "note": "Questi sono i tasti predefiniti di {release}. [W] [A] [S] [D] e [SPACE] sono i tasti «{movement}» del gioco stesso; gli altri sono sotto «{flight}» e «{helm}». Puoi cambiarli tutti in {path}.",
        "layout": "I tasti sono indicati in base alla loro posizione su una tastiera americana. La tua può etichettare lo stesso tasto in modo diverso; «{keybinds}» mostra ciascuno con il nome che gli dà la tua tastiera.",
    },
    "ar": {
        "title": "طريقة التحكم في Cherry",
        "desc": "كيف تقود Stratos-900 وAegis-X وتُبحر بسفن فئتي Leviathan وDreadnought: المفاتيح الافتراضية وما تفعله.",
        "note": "هذه هي المفاتيح الافتراضية في {release}. [W] [A] [S] [D] و[SPACE] هي مفاتيح «{movement}» في اللعبة نفسها، والباقي ضمن «{flight}» و«{helm}». يمكنك تغييرها كلها من {path}.",
        "layout": "أسماء المفاتيح هنا بحسب مواضعها في لوحة المفاتيح الأمريكية. قد تحمل لوحتك المفتاح نفسه باسم آخر، وتعرض شاشة «{keybinds}» كل مفتاح بالاسم الذي تعطيه له لوحتك.",
    },
    "ru": {
        "title": "Управление в Cherry",
        "desc": "Как летать на Stratos-900 и Aegis-X и водить корабли классов Leviathan и Dreadnought: клавиши по умолчанию и что они делают.",
        "note": "Это клавиши {release} по умолчанию. [W] [A] [S] [D] и [SPACE] — собственные клавиши игры из группы «{movement}»; остальные — в группах «{flight}» и «{helm}». Изменить любую можно в разделе {path}.",
        "layout": "Клавиши названы по их месту на американской клавиатуре. На вашей та же клавиша может быть подписана иначе; в разделе «{keybinds}» каждая показана так, как её называет ваша раскладка.",
    },
    "id": {
        "title": "Kontrol Cherry",
        "desc": "Cara menerbangkan Stratos-900 dan Aegis-X serta melayarkan kapal kelas Leviathan dan Dreadnought: tombol bawaan dan fungsinya.",
        "note": "Ini tombol bawaan {release}. [W] [A] [S] [D] dan [SPACE] adalah tombol “{movement}” milik game itu sendiri; sisanya ada di “{flight}” dan “{helm}”. Semuanya bisa diubah di {path}.",
        "layout": "Tombol disebut menurut letaknya pada papan ketik AS. Papan ketikmu bisa menandai tombol yang sama secara berbeda; “{keybinds}” menampilkan setiap tombol dengan nama dari papan ketikmu.",
    },
    "de": {
        "title": "Cherry-Steuerung",
        "desc": "So fliegst du die Stratos-900 und die Aegis-X und fährst die Schiffe der Leviathan- und der Dreadnought-Klasse: die Standardtasten und was sie tun.",
        "note": "Das sind die Standardtasten von {release}. [W] [A] [S] [D] und [SPACE] sind die eigenen „{movement}“-Tasten des Spiels; die übrigen stehen unter „{flight}“ und „{helm}“. Ändern kannst du alle unter {path}.",
        "layout": "Die Tasten sind nach ihrer Lage auf einer US-Tastatur benannt. Auf einer deutschen QWERTZ-Tastatur sind zum Beispiel [Z] und [Y] vertauscht; „{keybinds}“ zeigt jede Taste unter dem Namen, den deine Tastatur ihr gibt.",
    },
    "tr": {
        "title": "Cherry kontrolleri",
        "desc": "Stratos-900 ve Aegis-X nasıl uçurulur, Leviathan ve Dreadnought sınıfı gemiler nasıl yönetilir: varsayılan tuşlar ve işlevleri.",
        "note": "Bunlar {release} sürümünün varsayılan tuşlarıdır. [W] [A] [S] [D] ve [SPACE], oyunun kendi “{movement}” tuşlarıdır; diğerleri “{flight}” ve “{helm}” altındadır. Hepsini {path} içinde değiştirebilirsiniz.",
        "layout": "Tuşlar ABD klavyesindeki yerlerine göre adlandırılmıştır. Sizin klavyenizde aynı tuş başka bir adla işaretli olabilir; “{keybinds}” her tuşu klavyenizin verdiği adla gösterir.",
    },
}

TOKEN = re.compile(r"\[([^\]]+)\]|⟨([^⟩]+)⟩|\{(path|release)\}")
# Product names never break at their hyphen ("Stratos-" / "900" on a phone).
NO_BREAK = ("Stratos-900", "Aegis-X")
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
ARABIC = re.compile(r"[؀-ۿ]")


def _keys(text: str) -> list[str]:
    """The keys a string names, in order ([...] only)."""
    return [m.group(1) for m in TOKEN.finditer(text) if m.group(1) is not None]


def _fill(text: str, lang: str) -> str:
    """Put the per-language names into a note; {path} stays for _inline, which renders it."""
    flight, helm = CATEGORIES.get(lang, CATEGORIES_EN)
    return (text.replace("{movement}", MOVEMENT[lang]).replace("{flight}", flight)
            .replace("{helm}", helm).replace("{keybinds}", PATH[lang][2]))


def _inline(text: str, lang: str) -> str:
    """Escape the text; [K] becomes a key cap, the angle brackets an English span, {path} the menu path."""
    out, at = [], 0
    for m in TOKEN.finditer(text):
        out.append(esc(text[at:m.start()]))
        if m.group(1) is not None:
            label = KEYCAP[lang].get(m.group(1), m.group(1))
            # Keys read left to right on every page, except a name written in Arabic, which
            # reads the way the Arabic game prints it ("Alt الأيسر").
            direction = "rtl" if ARABIC.search(label) else "ltr"
            out.append('<kbd class="cc-key" dir="%s">%s</kbd>' % (direction, esc(label)))
        elif m.group(2) is not None:
            out.append('<span lang="en" dir="ltr">%s</span>' % esc(m.group(2)))
        elif m.group(3) == "release":
            # One left-to-right unit, so the Arabic page prints "Cherry 1.1.2", not "1.1.2 Cherry".
            out.append('<span lang="en" dir="ltr">Cherry %s</span>' % esc(CONTROLS_FOR))
        else:
            out.append('<span class="cc-path">%s</span>' % " › ".join(
                '<span class="cc-step">%s</span>' % esc(step) for step in PATH[lang]))
        at = m.end()
    out.append(esc(text[at:]))
    html = "".join(out)
    for name in NO_BREAK:
        html = html.replace(esc(name), '<span class="cc-nb">%s</span>' % esc(name))
    return html


def _slots(lang: str) -> list[tuple[str, str]]:
    """Every structured string of one language's cards, with a stable name for where it sits."""
    c = CONTROLS[lang]
    slots = []
    for card in ("air", "sea"):
        part = c[card]
        slots.append(("%s.title" % card, part["title"]))
        slots += [("%s.facts[%d]" % (card, i), fact) for i, fact in enumerate(part["facts"])]
        for i, (action, how) in enumerate(part["keys"]):
            slots += [("%s.keys[%d].action" % (card, i), action), ("%s.keys[%d].how" % (card, i), how)]
        for i, (title, items) in enumerate(part["lists"]):
            slots.append(("%s.lists[%d].title" % (card, i), title))
            slots += [("%s.lists[%d][%d]" % (card, i, j), item) for j, item in enumerate(items)]
    return slots


def problems_in(langs: list[str]) -> list[str]:
    """Everything that would make a page wrong in a way nothing else would notice."""
    problems = []
    english = [(name, sorted(_keys(text))) for name, text in _slots("en")]
    named = {k for _name, text in _slots("en") for k in _keys(text)}
    for missing in sorted((MOD_KEYS | MOVEMENT_KEYS) - named):
        problems.append("en: the cards never name the key %r -- a binding the game has is missing from the page" % missing)
    for lang in langs:
        for table, where in ((CONTROLS, "CONTROLS"), (INTRO, "INTRO"), (PATH, "PATH"), (KEYCAP, "KEYCAP"),
                             (MOVEMENT, "MOVEMENT")):
            if lang not in table:
                problems.append("%s: no %s entry (no fallback by design)" % (lang, where))
        if any(lang not in table for table in (CONTROLS, INTRO, PATH, KEYCAP, MOVEMENT)):
            continue
        mine = [(name, sorted(_keys(text))) for name, text in _slots(lang)]
        if [name for name, _k in mine] != [name for name, _k in english]:
            problems.append("%s: the cards do not have the English shape" % lang)
            continue
        for (name, keys), (_n, want) in zip(mine, english):
            if keys != want:
                problems.append("%s %s: names the keys %s where English names %s" % (lang, name, keys, want))
        texts = [text for _name, text in _slots(lang)] + [INTRO[lang][k] for k in ("title", "desc", "note", "layout")]
        for text in texts:
            for key in _keys(text):
                if key not in KNOWN_KEYS:
                    problems.append("%s: [%s] is not a key this page knows (%r)" % (lang, key, text[:60]))
            # A line about one release ("In 1.1.2, astern gives no thrust") must not survive onto
            # the page of the next: every version the copy names is the one it was read from.
            for version in VERSION.findall(text):
                if version != CONTROLS_FOR:
                    problems.append("%s: the copy speaks of %s, but the controls were read from %s (%r)"
                                    % (lang, version, CONTROLS_FOR, text[:60]))
        if "{release}" not in INTRO[lang]["note"]:
            problems.append("%s: the note does not say which version the page describes" % lang)
        for key in ("title", "desc", "note", "layout"):
            if not INTRO[lang].get(key):
                problems.append("%s: INTRO has no %s" % (lang, key))
        if lang != "en" and INTRO[lang]["note"] == INTRO["en"]["note"]:
            problems.append("%s: the note is the English one" % lang)
    return problems


# ★ NOT a format string, for the reason build_cherry.py gives: __ROOT__ is replaced with
#   str.replace(), and main() refuses a page that still holds it.
HEAD = """<link rel="stylesheet" href="__ROOT__assets/css/cherry-tokens.css">
<style>
.cc-wrap{background:var(--ch-bg);color:var(--ch-text);padding:3.5rem 1rem 5rem;
  margin:0 calc(50% - 50vw);width:100vw}
.cc-inner{max-width:48rem;margin:0 auto}
.cc-eyebrow{margin:0 0 .6rem;font-size:.8rem;letter-spacing:.16em;text-transform:uppercase}
.cc-eyebrow a{color:var(--ch-petal-deep);text-decoration:none;display:inline-flex;
  align-items:center;min-height:var(--tap,44px)}
.cc-eyebrow a:hover,.cc-eyebrow a:focus-visible{color:var(--ch-petal);text-decoration:underline;
  text-underline-offset:.3em}
.cc-eyebrow a:focus-visible{outline:2px solid var(--ch-petal);outline-offset:3px}
.cc-title{font-size:clamp(2.2rem,6vw,3.3rem);line-height:1.1;margin:0 0 1.2rem;
  letter-spacing:-.01em;color:var(--ch-petal)}
.cc-note{margin:0 0 .75rem;font-size:.98rem;line-height:1.8;color:var(--ch-text)}
.cc-note.cc-layout{color:var(--ch-text-muted);font-size:.92rem}
.cc-path{white-space:normal}
.cc-nb{white-space:nowrap}
.cc-step{font-weight:600;color:var(--ch-petal)}
.cc-card{margin:2.25rem 0 0;padding:clamp(1.25rem,4vw,2rem);border-radius:18px;
  background:var(--ch-bg-lift);border:1px solid var(--ch-line)}
.cc-h2{margin:0 0 1rem;padding:0;border:0;font-size:clamp(1.2rem,3.4vw,1.45rem);
  line-height:1.4;color:var(--ch-petal)}
/* style.css marks every h2 with the site's aurora-green bar; these pages are in the Cherry colours */
.cc-h2::before{content:none}
.cc-h3{margin:1.75rem 0 .6rem;padding:0;border:0;font-size:1rem;line-height:1.5;
  color:var(--ch-petal-deep)}
.cc-list{margin:0;padding-inline-start:1.2rem;line-height:1.8}
.cc-list li{margin:.35rem 0;color:var(--ch-text)}
.cc-list li::marker{color:var(--ch-blush)}
.cc-keys{width:100%;margin:1.25rem 0 0;border-collapse:collapse;font-size:.95rem;
  line-height:1.7}
/* style.css sets every th in small muted capitals (and uppercase Turkish would print a
   dotted capital I); these are action names, read as sentences, in the page's own case */
.cc-keys th,.cc-keys td{padding:.7rem 0;border-top:1px solid var(--ch-line);border-bottom:0;
  vertical-align:top;text-align:start;background:none}
.cc-keys th{width:34%;padding-inline-end:1rem;font-weight:600;color:var(--ch-text);
  font-size:inherit;text-transform:none;letter-spacing:normal}
.cc-keys td{color:var(--ch-text)}
.cc-key{display:inline-block;min-width:1.9em;margin:0 .1em;padding:0 .45em;
  border:1px solid rgba(__HALO_RGB__,.5);border-bottom-width:2px;border-radius:6px;
  background:rgba(__HALO_RGB__,.08);color:var(--ch-petal);text-align:center;
  font:600 .86em/1.65 ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  white-space:nowrap;box-shadow:none}
@media (max-width:34rem){
  .cc-keys th,.cc-keys td{display:block;width:auto;padding-inline-end:0}
  .cc-keys th{padding-bottom:.1rem}
  .cc-keys td{border-top:0;padding-top:0}
}
</style>"""
HALO_RGB = "232,180,198"


def head_css(root: str) -> str:
    return HEAD.replace("__ROOT__", root).replace("__HALO_RGB__", HALO_RGB)


def _card(lang: str, key: str) -> str:
    part = CONTROLS[lang][key]
    anchor = "cc-" + key
    facts = "".join("<li>%s</li>" % _inline(fact, lang) for fact in part["facts"])
    rows = "".join('<tr><th scope="row">%s</th><td>%s</td></tr>' % (_inline(action, lang), _inline(how, lang))
                   for action, how in part["keys"])
    lists = "".join('<h3 class="cc-h3">%s</h3><ul class="cc-list">%s</ul>'
                    % (_inline(title, lang), "".join("<li>%s</li>" % _inline(item, lang) for item in items))
                    for title, items in part["lists"])
    return ('<section class="cc-card" aria-labelledby="%s"><h2 class="cc-h2" id="%s">%s</h2>'
            '<ul class="cc-list">%s</ul><table class="cc-keys"><tbody>%s</tbody></table>%s</section>'
            % (anchor, anchor, _inline(part["title"], lang), facts, rows, lists))


def build_body(lang: str) -> str:
    intro = INTRO[lang]
    return ('<div class="cc-wrap"><div class="cc-inner">'
            '<p class="cc-eyebrow"><a href="../%s" lang="en" dir="ltr">Cherry</a></p>'
            '<h1 class="cc-title">%s</h1>'
            '<p class="cc-note">%s</p><p class="cc-note cc-layout">%s</p>'
            '%s%s</div></div>'
            % (BRAND_SECTION, esc(CONTROLS[lang]["heading"]), _inline(_fill(intro["note"], lang), lang),
               _inline(_fill(intro["layout"], lang), lang), _card(lang, "air"), _card(lang, "sea")))


def link_label(lang: str) -> str:
    """The brand page's link to this one says what this page's heading says (build_cherry.py)."""
    return CONTROLS[lang]["heading"]


def _newest_release() -> str | None:
    found = [RELEASE_RE.match(p.name) for p in (ROOT / "downloads").glob("Cherry_MODs_v*.zip")]
    versions = [m.group("ver") for m in found if m]
    return max(versions, key=lambda v: tuple(int(x) for x in v.split(".")), default=None)


def main() -> int:
    langs = available_langs()
    newest = _newest_release()
    if newest != CONTROLS_FOR:
        raise SystemExit(
            "ERROR: build_cherry_controls: the controls were read from Cherry %s's code, but the newest "
            "Cherry zip in downloads/ is %s. Read the keys and rules again against that version's code, "
            "correct the copy, then move CONTROLS_FOR." % (CONTROLS_FOR, newest))
    problems = problems_in(langs)
    if problems:
        raise SystemExit("ERROR: build_cherry_controls:\n  " + "\n  ".join(problems))
    for lang in langs:
        root = asset_root_prefix(1, lang)
        body = build_body(lang)
        # Nothing of the markup may survive into what a reader sees, and nothing may fall back.
        text_only = re.sub(r"<[^>]+>", "", body)
        for leftover in ("[", "]", "⟨", "⟩", "{", "}", "__"):
            if leftover in text_only:
                raise SystemExit("ERROR: build_cherry_controls: %s shows %r to the reader." % (lang, leftover))
        html = page(
            lang=lang,
            section=SECTION,
            title=INTRO[lang]["title"],
            description=INTRO[lang]["desc"],
            active="cherry",
            body=body,
            depth=1,
            extra_head=head_css(root),
        )
        if "__ROOT__" in html or "__HALO_RGB__" in html or "{{" in html:
            raise SystemExit("ERROR: build_cherry_controls: %s still holds a substitution token." % lang)
        target = ROOT / ("" if lang == "ja" else lang) / SECTION / "index.html"
        for rel in (root + "assets/css/cherry-tokens.css", "../" + BRAND_SECTION + "index.html"):
            if not (target.parent / rel).resolve().is_file():
                raise SystemExit("ERROR: build_cherry_controls: %s links %s, which is not there." % (lang, rel))
        if html.count('<kbd class="cc-key"') < 40:
            raise SystemExit("ERROR: build_cherry_controls: %s has fewer than 40 key caps -- the cards "
                             "did not render." % lang)
        write_page(lang, SECTION, html)
    # The brand page's one way here must arrive here, in every language (build_cherry.py
    # writes it before this runs; a link to a page that is not there is a quiet 404).
    for lang in langs:
        brand = ROOT / ("" if lang == "ja" else lang) / BRAND_SECTION / "index.html"
        link = '<a class="ch-more-link" href="../%s">%s</a>' % (SECTION, esc(link_label(lang)))
        if link not in brand.read_text(encoding="utf-8"):
            raise SystemExit("ERROR: build_cherry_controls: %s has no link %r." % (brand.relative_to(ROOT), link))
        here = (brand.parent / ("../" + SECTION) / "index.html").resolve()
        if here != (ROOT / ("" if lang == "ja" else lang) / SECTION / "index.html").resolve() or not here.is_file():
            raise SystemExit("ERROR: build_cherry_controls: %s's link resolves to %s." % (lang, here))
    print("build_cherry_controls: %d language(s), controls read from Cherry %s"
          % (len(langs), CONTROLS_FOR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
