#!/usr/bin/env python3
"""Builds index.html (home page) for every language.

Owner directive (2026-09-10, verbatim):

    「CorvusのホームについてもAI生成画像等を使用するなどして、迫力あ率つも
      Appleらしさを追求した方法でCorvusのできることを説明してください。
      展開しているブランドに関して言及することも良いでしょう。ただし
      シンプルかつ洗練された説明文に留めることです。」
    「全体的にテーマがスカイブルーではなく、以前のAuroraテーマが残っている
      のでこれも含めて改善をしてください。」

So the home page is an Apple product page now, top to bottom:

  0. the OPENING — the mark and the wordmark resolving out of the dark. This
     is scene 0 of the six-scene film that used to be the whole page, kept
     exactly: assets/css/hero-mark.css + assets/js/hero-mark.js build the
     arrival on top of the markup, classes and ids emitted here (they select
     `.film__scene--title .film__mark.hm`, `#filmWord .hm-g`, `.film__word`
     and `.film__stage:not(.is-live)`), so none of those names may change.
     One tagline was added under the wordmark.
  1. what it is        — headline, one line, the General pane at window size
  2. always current    — headline, one line, the Update pane (4.3.7 -> 4.3.8)
  3. verified          — three short rules in a glass strip, text only
  4. the brands        — OUKA / Cherry / Alpha ranked, Aureum on its own line
  5. sign-off          — the mark and two buttons: Get Corvus, Get Alpha

The five other scenes of the film (the arrival, the fan, the dissolve, the
sheet, the sign-off) are gone, and with them their five Corvus 1.5.2 frames,
the pinned-stage CSS in style.css and the film module in main.js. Sections
reveal on scroll through main.js's existing `.reveal` system — every
`main > section:not(.film)` is already one of its targets — so this page adds
no observer of its own, and with JS off or under prefers-reduced-motion
everything is simply visible where it stands.

IMAGERY. There is no video, no canvas, no library and no image-generation
model behind this page. The two pictures are real captures of Corvus 2.0.0 on
macOS (a 760x720pt window at 2x, shot over a neutral sky-blue backdrop with
the account shown as a neutral "Player" monogram), re-encoded to WebP and set
in window-shaped cards lit from behind by CSS light fields. The "depth" the
owner asked for comes from the real translucent glass of the app's own
window, which is the most honest picture of Corvus there is.

COPY. Every string on the page lives in COPY below, in all 13 languages,
Japanese first (the owner's language), with no fallback — the `home` section
of the language bundles was deleted with the wordless film and is not
revived, because a builder-local dict is easier to keep in step with the
markup it feeds (same pattern as scripts/build_cherry.py). Tone: short
declaratives, no superlatives, no exclamation marks, nothing that is not
true of the shipping app. `{n}` in a string is the live module count from
site_common.module_counts(), never a hardcoded number.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    SITE_TITLE, load_bundle, page, write_page, available_langs,
    asset_root_prefix, esc, module_counts,
)

ROOT = Path(__file__).resolve().parent.parent

# Both frames are the real Corvus 2.0.0 window on macOS, 760x720pt captured at
# 2x, so their natural size is 1520x1440 — which is what the width/height
# attributes advertise so nothing shifts while they load. They were shot
# against a throwaway pack folder under a scratch directory, never a real
# home: every path the General pane renders is on screen at readable size.
FRAME_W, FRAME_H = 1520, 1440
FRAMES = {
    "general": "app-general.webp",   # General: Play, Liquid Glass, pack folder
    "update": "app-update.webp",     # Update: Alpha 4.3.7 installed, 4.3.8 ready
}

# --- copy -------------------------------------------------------------------
# Keys, in every language:
#   tagline
#   what_h, what_p            1. what it is
#   current_h, current_p      2. always current
#   verified_h, verified_p    3. verified — plus the strip's three items:
#   v1_h, v1_p, v2_h, v2_p, v3_h, v3_p
#   brands_h, brands_p        4. the brands — plus one line per brand:
#   ouka_p, cherry_p, alpha_p, aureum_p
#   get_corvus, get_alpha     5. the two buttons
# Brand names (Corvus, Alpha, Aureum, Cherry) are never translated.
COPY = {
    "ja": {
        "tagline": "Alpha のためのランチャー。",
        "what_h": "パックのすべてを、ひとつのウインドウに。",
        "what_p": "Corvus は Alpha（{n} のモジュール、ひとつのバージョン）を導入し、最新に保ちます。"
                  "macOS では、ウインドウは本物のガラス。デスクトップが、ぼかしを通して透けて見えます。",
        "current_h": "いつも、最新。",
        "current_p": "新しい Alpha は、ボタンひとつ先に。自動アップデートをオンにすれば、ひとりでに届きます。",
        "verified_h": "ファイルに触れる前に、検証。",
        "verified_p": "すべてのアップデートは、同じ三つの決まりに従います。",
        "v1_h": "SHA-256",
        "v1_p": "ダウンロードはすべてチェックサムと照合されます。一致しなければ、導入されません。",
        "v2_h": "まず、バックアップ",
        "v2_p": "何かを変える前に、いまの導入状態を保存します。",
        "v3_h": "スイッチはひとつ",
        "v3_p": "自動アップデートは、ひとつの設定です。初期状態ではオフ。",
        "brands_h": "四つのブランド。",
        "brands_p": "OUKA、Cherry、Alpha —— 上位から順に。Aureum は別ジャンルの Mod で、独自のバージョンで進みます。",
        "ouka_p": "Cherry の上に立つ、最上位のブランド。ご期待ください。",
        "alpha_p": "パックそのもの。{n} のモジュール、ひとつのバージョン。Corvus が導入し、最新に保ちます。",
        "aureum_p": "独立した、任意の Mod。選んだときにだけ導入され、以降は最新に保たれます。",
        "cherry_p": "Alpha の上位に位置するブランド。Alpha と併せて導入でき、バージョンは独立して進みます。",
        "get_corvus": "Corvus を入手",
        "get_alpha": "Alpha を入手",
    },
    "en": {
        "tagline": "The launcher for Alpha.",
        "what_h": "The whole pack, in one window.",
        "what_p": "Corvus installs Alpha, {n} modules at one version, and keeps it current. "
                  "On macOS the window is real glass: the desktop shows through, blurred.",
        "current_h": "Always current.",
        "current_p": "A new Alpha is one press away. With automatic updates on, it arrives by itself.",
        "verified_h": "Verified before it touches a file.",
        "verified_p": "Every update follows the same three rules.",
        "v1_h": "SHA-256",
        "v1_p": "Every download is checked against its checksum. If it does not match, it is not installed.",
        "v2_h": "Backup first",
        "v2_p": "The current install is saved before anything is changed.",
        "v3_h": "One switch",
        "v3_p": "Automatic updates are a single setting. Off by default.",
        "brands_h": "Four brands.",
        "brands_p": "OUKA, Cherry and Alpha, in that order of tier. Aureum is a different kind of mod, on its own version.",
        "ouka_p": "The highest tier, above Cherry. Coming soon.",
        "alpha_p": "The pack. {n} modules, one version, installed and kept current by Corvus.",
        "aureum_p": "A separate, optional mod. Installed only when you choose, and kept current from then on.",
        "cherry_p": "The tier above Alpha. It installs alongside Alpha and versions independently.",
        "get_corvus": "Get Corvus",
        "get_alpha": "Get Alpha",
    },
    "es": {
        "tagline": "El launcher para Alpha.",
        "what_h": "Todo el pack, en una sola ventana.",
        "what_p": "Corvus instala Alpha, {n} módulos en una sola versión, y lo mantiene al día. "
                  "En macOS la ventana es cristal de verdad: el escritorio se ve a través, desenfocado.",
        "current_h": "Siempre al día.",
        "current_p": "Un nuevo Alpha está a un solo clic. Con las actualizaciones automáticas activadas, llega por sí solo.",
        "verified_h": "Verificado antes de tocar un archivo.",
        "verified_p": "Cada actualización sigue las mismas tres reglas.",
        "v1_h": "SHA-256",
        "v1_p": "Cada descarga se comprueba contra su suma de verificación. Si no coincide, no se instala.",
        "v2_h": "Primero, la copia de seguridad",
        "v2_p": "La instalación actual se guarda antes de cambiar nada.",
        "v3_h": "Un solo interruptor",
        "v3_p": "Las actualizaciones automáticas son un único ajuste. Desactivado de forma predeterminada.",
        "brands_h": "Cuatro marcas.",
        "brands_p": "OUKA, Cherry y Alpha, en ese orden de nivel. Aureum es un mod de otro género, con su propia versión.",
        "ouka_p": "El nivel más alto, por encima de Cherry. Muy pronto.",
        "alpha_p": "El pack. {n} módulos, una sola versión, instalado y mantenido al día por Corvus.",
        "aureum_p": "Un mod independiente y opcional. Se instala solo cuando tú lo eliges, y desde entonces se mantiene al día.",
        "cherry_p": "El nivel por encima de Alpha. Se instala junto a Alpha y avanza con su propia versión.",
        "get_corvus": "Obtener Corvus",
        "get_alpha": "Obtener Alpha",
    },
    "fr": {
        "tagline": "Le launcher pour Alpha.",
        "what_h": "Tout le pack, dans une seule fenêtre.",
        "what_p": "Corvus installe Alpha, {n} modules en une seule version, et le garde à jour. "
                  "Sur macOS, la fenêtre est un vrai verre : le bureau apparaît au travers, flouté.",
        "current_h": "Toujours à jour.",
        "current_p": "Un nouvel Alpha est à un clic. Avec les mises à jour automatiques activées, il arrive de lui-même.",
        "verified_h": "Vérifié avant de toucher un fichier.",
        "verified_p": "Chaque mise à jour suit les trois mêmes règles.",
        "v1_h": "SHA-256",
        "v1_p": "Chaque téléchargement est comparé à sa somme de contrôle. S'il ne correspond pas, il n'est pas installé.",
        "v2_h": "La sauvegarde d'abord",
        "v2_p": "L'installation actuelle est enregistrée avant toute modification.",
        "v3_h": "Un seul interrupteur",
        "v3_p": "Les mises à jour automatiques tiennent en un réglage. Désactivé par défaut.",
        "brands_h": "Quatre marques.",
        "brands_p": "OUKA, Cherry et Alpha, dans cet ordre de niveau. Aureum est un mod d'un autre genre, avec sa propre version.",
        "ouka_p": "Le niveau le plus élevé, au-dessus de Cherry. Bientôt disponible.",
        "alpha_p": "Le pack. {n} modules, une seule version, installé et tenu à jour par Corvus.",
        "aureum_p": "Un mod distinct et facultatif. Installé seulement si vous le choisissez, puis tenu à jour.",
        "cherry_p": "Le niveau au-dessus d'Alpha. Il s'installe aux côtés d'Alpha et avance avec sa propre version.",
        "get_corvus": "Obtenir Corvus",
        "get_alpha": "Obtenir Alpha",
    },
    "zh": {
        "tagline": "为 Alpha 而生的启动器。",
        "what_h": "整个整合包，尽在一个窗口。",
        "what_p": "Corvus 安装 Alpha（{n} 个模块，同一版本），并保持其最新。"
                  "在 macOS 上，窗口是真正的玻璃：桌面透过模糊的窗口若隐若现。",
        "current_h": "始终最新。",
        "current_p": "新的 Alpha 只需一次点击。开启自动更新后，它会自行送达。",
        "verified_h": "在触及任何文件之前，先行验证。",
        "verified_p": "每一次更新都遵循同样的三条规则。",
        "v1_h": "SHA-256",
        "v1_p": "每个下载都会与其校验和比对。若不一致，则不予安装。",
        "v2_h": "先备份",
        "v2_p": "在改动任何内容之前，先保存当前的安装。",
        "v3_h": "一个开关",
        "v3_p": "自动更新只是一项设置。默认关闭。",
        "brands_h": "四个品牌。",
        "brands_p": "OUKA、Cherry、Alpha,依此为级别高低。Aureum 属于另一类 Mod,以独立的版本演进。",
        "ouka_p": "位于 Cherry 之上,最高级别的品牌。敬请期待。",
        "alpha_p": "整合包本身。{n} 个模块，同一版本，由 Corvus 安装并保持最新。",
        "aureum_p": "一个独立的可选 Mod。仅在你选择时安装，此后保持最新。",
        "cherry_p": "位于 Alpha 之上的品牌。可与 Alpha 一同安装，版本各自独立演进。",
        "get_corvus": "获取 Corvus",
        "get_alpha": "获取 Alpha",
    },
    "ko": {
        "tagline": "Alpha를 위한 런처.",
        "what_h": "팩 전체를, 하나의 창에.",
        "what_p": "Corvus는 Alpha({n}개 모듈, 하나의 버전)를 설치하고 최신 상태로 유지합니다. "
                  "macOS에서는 창이 진짜 유리입니다. 데스크톱이 흐릿하게 비쳐 보입니다.",
        "current_h": "언제나 최신.",
        "current_p": "새 Alpha는 버튼 하나 거리에 있습니다. 자동 업데이트를 켜 두면, 저절로 도착합니다.",
        "verified_h": "파일에 손대기 전에, 검증.",
        "verified_p": "모든 업데이트는 같은 세 가지 규칙을 따릅니다.",
        "v1_h": "SHA-256",
        "v1_p": "모든 다운로드는 체크섬과 대조됩니다. 일치하지 않으면 설치되지 않습니다.",
        "v2_h": "먼저 백업",
        "v2_p": "무엇이든 바꾸기 전에, 현재 설치 상태를 저장합니다.",
        "v3_h": "스위치 하나",
        "v3_p": "자동 업데이트는 설정 하나입니다. 기본값은 꺼짐.",
        "brands_h": "네 가지 브랜드.",
        "brands_p": "OUKA, Cherry, Alpha 순으로 상위 브랜드입니다. Aureum은 장르가 다른 모드로, 자체 버전으로 나아갑니다.",
        "ouka_p": "Cherry 위에 서는 최상위 브랜드입니다. 기대해 주세요.",
        "alpha_p": "팩 그 자체. {n}개 모듈, 하나의 버전. Corvus가 설치하고 최신 상태로 유지합니다.",
        "aureum_p": "별도의 선택형 모드입니다. 직접 선택했을 때만 설치되며, 그 후로는 최신 상태로 유지됩니다.",
        "cherry_p": "Alpha 위에 자리한 브랜드입니다. Alpha와 함께 설치할 수 있으며, 버전은 각자 독립적으로 나아갑니다.",
        "get_corvus": "Corvus 받기",
        "get_alpha": "Alpha 받기",
    },
    "pt-br": {
        "tagline": "O launcher para o Alpha.",
        "what_h": "O pack inteiro, em uma só janela.",
        "what_p": "O Corvus instala o Alpha, {n} módulos em uma única versão, e o mantém atualizado. "
                  "No macOS, a janela é vidro de verdade: a área de trabalho aparece através dela, desfocada.",
        "current_h": "Sempre atualizado.",
        "current_p": "Um novo Alpha está a um toque de distância. Com as atualizações automáticas ligadas, ele chega sozinho.",
        "verified_h": "Verificado antes de tocar em um arquivo.",
        "verified_p": "Toda atualização segue as mesmas três regras.",
        "v1_h": "SHA-256",
        "v1_p": "Cada download é conferido com sua soma de verificação. Se não bater, não é instalado.",
        "v2_h": "Backup primeiro",
        "v2_p": "A instalação atual é salva antes de qualquer alteração.",
        "v3_h": "Um único interruptor",
        "v3_p": "As atualizações automáticas são um único ajuste. Desligado por padrão.",
        "brands_h": "Quatro marcas.",
        "brands_p": "OUKA, Cherry e Alpha, nessa ordem de nível. Aureum é um mod de outro gênero, com sua própria versão.",
        "ouka_p": "O nível mais alto, acima do Cherry. Em breve.",
        "alpha_p": "O pack. {n} módulos, uma única versão, instalado e mantido atualizado pelo Corvus.",
        "aureum_p": "Um mod separado e opcional. Instalado só quando você escolhe, e mantido atualizado a partir daí.",
        "cherry_p": "O nível acima do Alpha. Instala-se ao lado do Alpha e avança com versão própria.",
        "get_corvus": "Obter o Corvus",
        "get_alpha": "Obter o Alpha",
    },
    "it": {
        "tagline": "Il launcher per Alpha.",
        "what_h": "Tutto il pack, in una sola finestra.",
        "what_p": "Corvus installa Alpha, {n} moduli in una sola versione, e lo tiene aggiornato. "
                  "Su macOS la finestra è vetro vero: la scrivania traspare, sfocata.",
        "current_h": "Sempre aggiornato.",
        "current_p": "Un nuovo Alpha è a un solo clic. Con gli aggiornamenti automatici attivi, arriva da sé.",
        "verified_h": "Verificato prima di toccare un file.",
        "verified_p": "Ogni aggiornamento segue le stesse tre regole.",
        "v1_h": "SHA-256",
        "v1_p": "Ogni download viene confrontato con il suo checksum. Se non corrisponde, non viene installato.",
        "v2_h": "Prima il backup",
        "v2_p": "L'installazione attuale viene salvata prima di cambiare qualsiasi cosa.",
        "v3_h": "Un solo interruttore",
        "v3_p": "Gli aggiornamenti automatici sono una sola impostazione. Disattivata per impostazione predefinita.",
        "brands_h": "Quattro marchi.",
        "brands_p": "OUKA, Cherry e Alpha, in quest'ordine di livello. Aureum è un mod di altro genere, con la propria versione.",
        "ouka_p": "Il livello più alto, sopra Cherry. In arrivo.",
        "alpha_p": "Il pack. {n} moduli, una sola versione, installato e tenuto aggiornato da Corvus.",
        "aureum_p": "Una mod separata e facoltativa. Installata solo quando lo scegli, e da allora tenuta aggiornata.",
        "cherry_p": "Il livello sopra Alpha. Si installa accanto ad Alpha e avanza con una versione propria.",
        "get_corvus": "Ottieni Corvus",
        "get_alpha": "Ottieni Alpha",
    },
    "ar": {
        "tagline": "المشغّل المخصّص لـ Alpha.",
        "what_h": "الحزمة كلّها، في نافذة واحدة.",
        "what_p": "يثبّت Corvus حزمة Alpha، {n} وحدة بإصدار واحد، ويبقيها محدّثة. "
                  "على macOS النافذة زجاج حقيقي: يظهر سطح المكتب من خلالها، مموّهاً.",
        "current_h": "محدّث دائماً.",
        "current_p": "إصدار Alpha الجديد على بُعد ضغطة واحدة. ومع تفعيل التحديثات التلقائية، يصل من تلقاء نفسه.",
        "verified_h": "يُتحقّق منه قبل أن يمسّ أيّ ملف.",
        "verified_p": "كل تحديث يتّبع القواعد الثلاث نفسها.",
        "v1_h": "SHA-256",
        "v1_p": "يُقارَن كل تنزيل بمجموع التحقّق الخاص به. وإن لم يتطابق، لا يُثبَّت.",
        "v2_h": "النسخ الاحتياطي أولاً",
        "v2_p": "يُحفَظ التثبيت الحالي قبل تغيير أي شيء.",
        "v3_h": "مفتاح واحد",
        "v3_p": "التحديثات التلقائية إعداد واحد. معطّل افتراضياً.",
        "brands_h": "أربع علامات.",
        "brands_p": "OUKA و Cherry و Alpha، بهذا الترتيب من حيث المستوى. أما Aureum فهو نوع مختلف من الإضافات، بإصداره الخاص.",
        "ouka_p": "المستوى الأعلى، فوق Cherry. ترقّبوا قريباً.",
        "alpha_p": "الحزمة نفسها. {n} وحدة بإصدار واحد، يثبّتها Corvus ويبقيها محدّثة.",
        "aureum_p": "مود منفصل واختياري. لا يُثبَّت إلا حين تختار ذلك، ثم يبقى محدّثاً بعدها.",
        "cherry_p": "المستوى الأعلى من Alpha. يُثبَّت إلى جانب Alpha ويتقدّم بإصدار مستقل.",
        "get_corvus": "احصل على Corvus",
        "get_alpha": "احصل على Alpha",
    },
    "ru": {
        "tagline": "Лаунчер для Alpha.",
        "what_h": "Весь пак, в одном окне.",
        "what_p": "Corvus устанавливает Alpha, {n} модулей одной версии, и держит его актуальным. "
                  "На macOS окно — настоящее стекло: сквозь него, размытым, виден рабочий стол.",
        "current_h": "Всегда актуально.",
        "current_p": "Новый Alpha — в одном нажатии. С включёнными автообновлениями он приходит сам.",
        "verified_h": "Проверено до того, как тронут хоть один файл.",
        "verified_p": "Каждое обновление следует одним и тем же трём правилам.",
        "v1_h": "SHA-256",
        "v1_p": "Каждая загрузка сверяется со своей контрольной суммой. Если она не совпадает, установка не выполняется.",
        "v2_h": "Сначала резервная копия",
        "v2_p": "Текущая установка сохраняется до того, как что-либо будет изменено.",
        "v3_h": "Один переключатель",
        "v3_p": "Автообновления — одна настройка. По умолчанию выключена.",
        "brands_h": "Четыре бренда.",
        "brands_p": "OUKA, Cherry и Alpha — именно в этом порядке уровней. Aureum — мод другого рода, со своей версией.",
        "ouka_p": "Высший уровень — выше Cherry. Уже скоро.",
        "alpha_p": "Сам пак. {n} модулей, одна версия; Corvus устанавливает его и держит актуальным.",
        "aureum_p": "Отдельный необязательный мод. Устанавливается только по вашему выбору и с тех пор держится актуальным.",
        "cherry_p": "Уровень выше Alpha. Устанавливается рядом с Alpha и развивается в собственной версии.",
        "get_corvus": "Получить Corvus",
        "get_alpha": "Получить Alpha",
    },
    "id": {
        "tagline": "Launcher untuk Alpha.",
        "what_h": "Seluruh pack, dalam satu jendela.",
        "what_p": "Corvus memasang Alpha, {n} modul dalam satu versi, dan menjaganya tetap mutakhir. "
                  "Di macOS, jendelanya kaca sungguhan: desktop tampak menembusnya, dengan buram.",
        "current_h": "Selalu mutakhir.",
        "current_p": "Alpha yang baru hanya satu tekanan jauhnya. Dengan pembaruan otomatis aktif, ia tiba dengan sendirinya.",
        "verified_h": "Diverifikasi sebelum menyentuh satu berkas pun.",
        "verified_p": "Setiap pembaruan mengikuti tiga aturan yang sama.",
        "v1_h": "SHA-256",
        "v1_p": "Setiap unduhan dicocokkan dengan checksum-nya. Jika tidak cocok, tidak dipasang.",
        "v2_h": "Cadangkan dulu",
        "v2_p": "Pemasangan saat ini disimpan sebelum apa pun diubah.",
        "v3_h": "Satu sakelar",
        "v3_p": "Pembaruan otomatis hanyalah satu pengaturan. Nonaktif secara bawaan.",
        "brands_h": "Empat merek.",
        "brands_p": "OUKA, Cherry, dan Alpha, dalam urutan tingkat itu. Aureum adalah mod jenis lain, dengan versinya sendiri.",
        "ouka_p": "Tingkat tertinggi, di atas Cherry. Segera hadir.",
        "alpha_p": "Pack itu sendiri. {n} modul, satu versi, dipasang dan dijaga tetap mutakhir oleh Corvus.",
        "aureum_p": "Mod terpisah dan opsional. Dipasang hanya saat Anda memilihnya, lalu dijaga tetap mutakhir.",
        "cherry_p": "Tingkat di atas Alpha. Terpasang berdampingan dengan Alpha dan melaju dengan versinya sendiri.",
        "get_corvus": "Dapatkan Corvus",
        "get_alpha": "Dapatkan Alpha",
    },
    "de": {
        "tagline": "Der Launcher für Alpha.",
        "what_h": "Das ganze Pack, in einem Fenster.",
        "what_p": "Corvus installiert Alpha, {n} Module in einer Version, und hält es aktuell. "
                  "Auf macOS ist das Fenster echtes Glas: Der Schreibtisch scheint hindurch, unscharf.",
        "current_h": "Immer aktuell.",
        "current_p": "Ein neues Alpha ist einen Klick entfernt. Mit eingeschalteten automatischen Updates kommt es von selbst.",
        "verified_h": "Geprüft, bevor eine Datei berührt wird.",
        "verified_p": "Jedes Update folgt denselben drei Regeln.",
        "v1_h": "SHA-256",
        "v1_p": "Jeder Download wird mit seiner Prüfsumme abgeglichen. Stimmt sie nicht, wird nichts installiert.",
        "v2_h": "Erst die Sicherung",
        "v2_p": "Die aktuelle Installation wird gesichert, bevor etwas verändert wird.",
        "v3_h": "Ein Schalter",
        "v3_p": "Automatische Updates sind eine einzige Einstellung. Standardmäßig aus.",
        "brands_h": "Vier Marken.",
        "brands_p": "OUKA, Cherry und Alpha, in dieser Rangfolge. Aureum ist eine andere Art von Mod, mit eigener Version.",
        "ouka_p": "Die höchste Stufe, über Cherry. Bald verfügbar.",
        "alpha_p": "Das Pack. {n} Module, eine Version, von Corvus installiert und aktuell gehalten.",
        "aureum_p": "Ein separater, optionaler Mod. Nur installiert, wenn Sie es wählen, und von da an aktuell gehalten.",
        "cherry_p": "Die Stufe über Alpha. Wird neben Alpha installiert und führt seine eigene Version.",
        "get_corvus": "Corvus laden",
        "get_alpha": "Alpha laden",
    },
    "tr": {
        "tagline": "Alpha için başlatıcı.",
        "what_h": "Paketin tamamı, tek bir pencerede.",
        "what_p": "Corvus, tek sürümde {n} modülden oluşan Alpha'yı kurar ve güncel tutar. "
                  "macOS'ta pencere gerçek camdır: masaüstü, bulanık biçimde arkasından görünür.",
        "current_h": "Her zaman güncel.",
        "current_p": "Yeni Alpha yalnızca bir dokunuş uzakta. Otomatik güncellemeler açıkken kendiliğinden gelir.",
        "verified_h": "Bir dosyaya dokunmadan önce doğrulanır.",
        "verified_p": "Her güncelleme aynı üç kurala uyar.",
        "v1_h": "SHA-256",
        "v1_p": "Her indirme, sağlama toplamıyla karşılaştırılır. Eşleşmezse kurulmaz.",
        "v2_h": "Önce yedek",
        "v2_p": "Herhangi bir şey değiştirilmeden önce mevcut kurulum kaydedilir.",
        "v3_h": "Tek anahtar",
        "v3_p": "Otomatik güncellemeler tek bir ayardır. Varsayılan olarak kapalı.",
        "brands_h": "Dört marka.",
        "brands_p": "OUKA, Cherry ve Alpha; seviye sırası budur. Aureum başka türden bir mod, kendi sürümüyle ilerler.",
        "ouka_p": "En üst seviye; Cherry'nin üzerinde. Çok yakında.",
        "alpha_p": "Paketin kendisi. {n} modül, tek sürüm; Corvus tarafından kurulur ve güncel tutulur.",
        "aureum_p": "Ayrı, isteğe bağlı bir mod. Yalnızca siz seçtiğinizde kurulur, sonrasında güncel tutulur.",
        "cherry_p": "Alpha'nın üzerindeki seviye. Alpha ile birlikte kurulur ve kendi sürümüyle ilerler.",
        "get_corvus": "Corvus'u edinin",
        "get_alpha": "Alpha'yı edinin",
    },
}

KEYS = (
    "tagline", "what_h", "what_p", "current_h", "current_p",
    "verified_h", "verified_p", "v1_h", "v1_p", "v2_h", "v2_p", "v3_h", "v3_p",
    "brands_h", "brands_p", "ouka_p", "alpha_p", "aureum_p", "cherry_p",
    "get_corvus", "get_alpha",
)


def frame_img(prefix: str, key: str, eager: bool = False) -> str:
    """One window capture. alt="" on purpose: the headline and the line above
    each frame say what it shows, and the picture is the object, not the
    text — so nothing in the image needs a 14th translation."""
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{prefix}assets/img/film/{FRAMES[key]}" alt="" '
            f'width="{FRAME_W}" height="{FRAME_H}" decoding="async" {loading}>')


def blossom_svg() -> str:
    """The Cherry mark, inlined so its <g class="ch-spin"> can turn (the same
    slow rotation the Cherry page runs, see scripts/build_cherry.py). The file
    carries width/height and a role/aria-label for standalone use; inside a
    tile that already says "Cherry" the graphic is decoration, so both go."""
    svg = (ROOT / "assets" / "img" / "cherry" / "blossom-mark.svg").read_text(encoding="utf-8")
    before = 'width="128" height="128" role="img" aria-label="Cherry"'
    if before not in svg:
        raise SystemExit("build_home: blossom-mark.svg no longer carries the "
                         "root attributes this builder rewrites; read blossom_svg()")
    return svg.replace(before, 'aria-hidden="true" focusable="false"')


# --- the opening -----------------------------------------------------------
# The mark. `.film__mark` keeps every dimension and colour style.css gives it;
# the nested spans are the extra light layers hero-mark.css composes the
# arrival out of, and they are display:none unless that file's `html.js` +
# `prefers-reduced-motion: no-preference` gate is satisfied. The three-deep
# halo is not over-engineering: CSS applies filters BEFORE masking on the same
# element, so the blur has to sit on an ancestor of the mask or the glow is
# clipped back to the mark's hard edge.
OPENING_MARK = """<span class="film__mark hm" aria-hidden="true">
        <span class="hm__bloom"></span>
        <span class="hm__halo"><span class="hm__halo-b"><span class="hm__halo-i"></span></span></span>
        <span class="hm__body">
          <span class="hm__plate"></span>
          <span class="hm__flow"></span>
          <span class="hm__rake"></span>
          <span class="hm__ambient"></span>
        </span>
      </span>"""


def wordmark(text: str) -> str:
    """The wordmark, one span per glyph, so the name can resolve letter by
    letter instead of as one block.

    Emitted at BUILD time rather than by hero-mark.js on purpose: the split
    then exists in the served HTML, so there is no moment where the DOM is
    rewritten under a running animation and nothing depends on a script to
    produce readable markup. hero-mark.js only decorates what is already here.

    Each WORD is wrapped as well, and hero-mark.css gives that wrapper
    `white-space: nowrap`: once the glyphs are inline-block, every glyph is
    its own line-break opportunity. The name is one word today; the loop is
    kept general so a two-word name would still carry a beat of silence
    across the gap (the space consumes an index of its own).
    """
    out = []
    i = 0
    words = text.split(" ")
    for w_index, w in enumerate(words):
        glyphs = "".join(
            f'<span class="hm-g" style="--i:{i + n}">{esc(ch)}</span>'
            for n, ch in enumerate(w)
        )
        i += len(w)
        out.append(f'<span class="hm-w">{glyphs}</span>')
        if w_index < len(words) - 1:
            out.append(" ")
            i += 1
    return "".join(out)


def build_lang(lang):
    bundle = load_bundle(lang)
    p = asset_root_prefix(0, lang)
    n_modules, _with_fabric = module_counts()
    c = {k: esc(v.replace("{n}", str(n_modules))) for k, v in COPY[lang].items()}

    # Page links. The home page sits at its language's root (ja at /, every
    # other language at /<lang>/), so "./alpha/" is the right Alpha page in
    # all 13 languages — exactly what site_common.page() uses for its own nav
    # at depth 0. Assets are different: they live at the SITE root, one
    # level up for non-ja, hence `p` above.
    lp = "./"

    body = f"""
<section class="film" aria-labelledby="filmWord">
  <div class="film__stage" id="filmStage">
    <!-- the mark and the name resolve out of the dark (hero-mark.css / .js) -->
    <div class="film__scene film__scene--title">
      {OPENING_MARK}
      <h1 class="film__word" id="filmWord" aria-label="{esc(SITE_TITLE)}">{wordmark(SITE_TITLE)}</h1>
      <p class="film__tagline">{c["tagline"]}</p>
    </div>
  </div>
</section>

<section class="home-beat" aria-labelledby="homeWhat">
  <div class="home-beat__head">
    <h2 id="homeWhat">{c["what_h"]}</h2>
    <p class="home-beat__lede">{c["what_p"]}</p>
  </div>
  <figure class="home-frame">{frame_img(p, "general", eager=True)}</figure>
</section>

<section class="home-beat" aria-labelledby="homeCurrent">
  <div class="home-beat__head">
    <h2 id="homeCurrent">{c["current_h"]}</h2>
    <p class="home-beat__lede">{c["current_p"]}</p>
  </div>
  <figure class="home-frame">{frame_img(p, "update")}</figure>
</section>

<section class="home-beat" aria-labelledby="homeVerified">
  <div class="home-beat__head">
    <h2 id="homeVerified">{c["verified_h"]}</h2>
    <p class="home-beat__lede">{c["verified_p"]}</p>
  </div>
  <ul class="home-strip">
    <li><h3>{c["v1_h"]}</h3><p>{c["v1_p"]}</p></li>
    <li><h3>{c["v2_h"]}</h3><p>{c["v2_p"]}</p></li>
    <li><h3>{c["v3_h"]}</h3><p>{c["v3_p"]}</p></li>
  </ul>
</section>

<section class="home-beat" aria-labelledby="homeBrands">
  <div class="home-beat__head">
    <h2 id="homeBrands">{c["brands_h"]}</h2>
    <p class="home-beat__lede">{c["brands_p"]}</p>
  </div>
  <div class="home-brands">
    <a class="card home-brand" href="{lp}ouka/">
      <span class="home-brand__art home-brand__art--ouka"><img src="{p}assets/img/ouka/mark-320.webp" alt="" width="320" height="303" loading="lazy" decoding="async"></span>
      <span class="home-brand__name">OUKA</span>
      <span class="home-brand__line">{c["ouka_p"]}</span>
    </a>
    <a class="card home-brand" href="{lp}cherry/">
      <span class="home-brand__art home-brand__art--cherry">{blossom_svg()}</span>
      <span class="home-brand__name">Cherry</span>
      <span class="home-brand__line">{c["cherry_p"]}</span>
    </a>
    <a class="card home-brand" href="{lp}alpha/">
      <span class="home-brand__art home-brand__art--alpha" aria-hidden="true">A</span>
      <span class="home-brand__name">Alpha</span>
      <span class="home-brand__line">{c["alpha_p"]}</span>
    </a>
    <a class="card home-brand home-brand--aureum" href="{lp}aureum/">
      <span class="home-brand__art home-brand__art--aureum"><img src="{p}assets/img/aureum/monogram.webp" alt="" width="584" height="455" loading="lazy" decoding="async"></span>
      <span class="home-brand__name">Aureum</span>
      <span class="home-brand__line">{c["aureum_p"]}</span>
    </a>
  </div>
</section>

<section class="home-cta">
  <span class="film__mark film__mark--sign" aria-hidden="true"></span>
  <div class="home-cta__row">
    <a class="btn" href="{lp}launcher/">{c["get_corvus"]}</a>
    <a class="btn btn--ghost" href="{lp}download/">{c["get_alpha"]}</a>
  </div>
</section>
"""
    # The opening beat, home page only: a page-scoped stylesheet plus a
    # deferred script, both addressed through asset_root_prefix() rather
    # than a hardcoded "../" (non-ja languages sit one directory deeper —
    # see the note on that helper for the 404 a hardcoded prefix caused).
    extra_head = (
        f'<link rel="stylesheet" href="{p}assets/css/hero-mark.css">\n'
        f'<script defer src="{p}assets/js/hero-mark.js"></script>\n'
    )

    html = page(
        lang=lang,
        section="",
        title="",
        description=bundle["ui"]["site_description"],
        active="home",
        body=body,
        depth=0,
        extra_head=extra_head,
    )
    write_page(lang, "", html)


def build():
    langs = available_langs()
    missing = [lang for lang in langs if lang not in COPY]
    if missing:
        raise SystemExit("build_home: no copy for %s (no fallback by design)"
                         % ", ".join(missing))
    for lang, c in COPY.items():
        gaps = [k for k in KEYS if not c.get(k)]
        if gaps:
            raise SystemExit("build_home: %s is missing %s" % (lang, ", ".join(gaps)))
        loud = [k for k, v in c.items() if "!" in v or "！" in v]
        if loud:
            raise SystemExit("build_home: %s has an exclamation mark in %s"
                             % (lang, ", ".join(loud)))
    for lang in langs:
        build_lang(lang)


if __name__ == "__main__":
    build()
