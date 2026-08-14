/* 全站多语言：中/英/西/法/德/葡/韩/日/俄/意 */
(function () {
    var LANGS = {
        en: {
            name: "English",
            dict: {
                "nav.about": "About",
                "hero.title": "Download Videos Online",
                "hero.subtitle": "YouTube · TikTok · Facebook · Pinterest Video Downloader",
                "hero.placeholder": "Paste video URL here",
                "hero.button": "Download",
                "ad.title": "Advertisement",
                "ad.sub": "Sponsored · Your Ad Here",
                "modal.processing": "Processing, please wait...",
                "card.mp4": "MP4 Download",
                "card.nowm": "No watermark",
                "card.fb": "Download FB Videos",
                "card.save": "Save Video",
                "notice.loading": "Loading...",
                "js.empty": "Please enter video URL",
                "js.network": "Network error, please try again",
                "js.failed": "Download failed",
                "js.dlimg": "Download Image",
                "js.dlthumb": "Download Thumbnail",
                "js.dlvideo": "Download Video",
                "js.dlaudio": "Download Audio",
                "step.1no": "Step 1",
                "step.1title": "Copy video link",
                "step.1desc": "Open YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, find the video you want to download, and copy the full link (URL) from the browser address bar.",
                "step.1copy": "Copy link",
                "step.2no": "Step 2",
                "step.2title": "Paste into the input box",
                "step.2desc": "Return to the homepage, paste the link into the search box. Any platform is supported, and the source website is detected automatically.",
                "step.2paste": "Paste video link here...",
                "step.3no": "Step 3",
                "step.3title": "Download and save",
                "step.3desc": "Click the Download button; a processing window will pop up shortly. Once parsed, you can download the video, audio and thumbnail to your device.",
                "info.platform": "Supported platforms",
                "info.downloads": "Downloads",
                "d.thumb": "Video thumbnail (JPG)",
                "d.video": "HD video (MP4)",
                "d.audio": "Separate audio (M4A/WebM)",
                "tiktok.nowm": "TikTok (no watermark)"
            }
        },
        zh: {
            name: "中文",
            dict: {
                "nav.about": "关于",
                "hero.title": "在线视频下载",
                "hero.subtitle": "YouTube · TikTok · Facebook · Pinterest 视频下载器",
                "hero.placeholder": "在此粘贴视频链接",
                "hero.button": "下载",
                "ad.title": "广告",
                "ad.sub": "赞助商 · 您的广告位置",
                "modal.processing": "正在处理，请稍候...",
                "card.mp4": "MP4 下载",
                "card.nowm": "无水印",
                "card.fb": "下载 FB 视频",
                "card.save": "保存视频",
                "notice.loading": "加载中...",
                "js.empty": "请输入视频链接",
                "js.network": "网络错误，请重试",
                "js.failed": "下载失败",
                "js.dlimg": "下载图片",
                "js.dlthumb": "下载缩略图",
                "js.dlvideo": "下载视频",
                "js.dlaudio": "下载音频",
                "step.1no": "第一步",
                "step.1title": "复制视频链接",
                "step.1desc": "打开 YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest，找到想下载的视频，复制浏览器地址栏中的完整链接（URL）。",
                "step.1copy": "复制链接",
                "step.2no": "第二步",
                "step.2title": "粘贴到输入框",
                "step.2desc": "返回本站主页，把链接粘贴到搜索框。支持任意一个平台，系统会自动识别来源网站。",
                "step.2paste": "在此粘贴视频链接...",
                "step.3no": "第三步",
                "step.3title": "点击下载并保存",
                "step.3desc": "点击下载按钮，稍候片刻将弹出处理窗口；解析完成后即可下载视频、音频与缩略图，保存到本地。",
                "info.platform": "支持平台",
                "info.downloads": "下载内容",
                "d.thumb": "🖼 视频缩略图（JPG）",
                "d.video": "🎬 高清视频（MP4）",
                "d.audio": "🎵 独立音频（M4A/WebM）",
                "tiktok.nowm": "TikTok（无水印）"
            }
        },
        es: {
            name: "Español",
            dict: {
                "nav.about": "Acerca de",
                "hero.title": "Descargar videos en línea",
                "hero.subtitle": "Descargador de videos YouTube · TikTok · Facebook · Pinterest",
                "hero.placeholder": "Pegue la URL del video aquí",
                "hero.button": "Descargar",
                "ad.title": "Publicidad",
                "ad.sub": "Patrocinado · Su anuncio aquí",
                "modal.processing": "Procesando, espere por favor...",
                "card.mp4": "Descargar MP4",
                "card.nowm": "Sin marca de agua",
                "card.fb": "Descargar videos de FB",
                "card.save": "Guardar video",
                "notice.loading": "Cargando...",
                "js.empty": "Por favor, introduzca la URL del video",
                "js.network": "Error de red, inténtelo de nuevo",
                "js.failed": "Error al descargar",
                "js.dlimg": "Descargar imagen",
                "js.dlthumb": "Descargar miniatura",
                "js.dlvideo": "Descargar video",
                "js.dlaudio": "Descargar audio",
                "step.1no": "Paso 1",
                "step.1title": "Copiar enlace del video",
                "step.1desc": "Abra YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, encuentre el video que desea descargar y copie el enlace completo (URL) de la barra de direcciones.",
                "step.1copy": "Copiar enlace",
                "step.2no": "Paso 2",
                "step.2title": "Pegar en el cuadro de entrada",
                "step.2desc": "Vuelva a la página principal, pegue el enlace en el cuadro de búsqueda. Se admite cualquier plataforma y la web de origen se detecta automáticamente.",
                "step.2paste": "Pegue aquí el enlace del video...",
                "step.3no": "Paso 3",
                "step.3title": "Descargar y guardar",
                "step.3desc": "Haga clic en el botón Descargar; aparecerá una ventana de procesamiento. Una vez analizado, puede descargar video, audio y miniatura a su dispositivo.",
                "info.platform": "Plataformas compatibles",
                "info.downloads": "Descargas",
                "d.thumb": "🖼 Miniatura del video (JPG)",
                "d.video": "🎬 Video en HD (MP4)",
                "d.audio": "🎵 Audio separado (M4A/WebM)",
                "tiktok.nowm": "TikTok (sin marca de agua)"
            }
        },
        fr: {
            name: "Français",
            dict: {
                "nav.about": "À propos",
                "hero.title": "Télécharger des vidéos en ligne",
                "hero.subtitle": "Téléchargeur de vidéos YouTube · TikTok · Facebook · Pinterest",
                "hero.placeholder": "Collez l'URL de la vidéo ici",
                "hero.button": "Télécharger",
                "ad.title": "Publicité",
                "ad.sub": "Sponsorisé · Votre publicité ici",
                "modal.processing": "Traitement en cours, veuillez patienter...",
                "card.mp4": "Télécharger MP4",
                "card.nowm": "Sans filigrane",
                "card.fb": "Télécharger les vidéos FB",
                "card.save": "Enregistrer la vidéo",
                "notice.loading": "Chargement...",
                "js.empty": "Veuillez saisir l'URL de la vidéo",
                "js.network": "Erreur réseau, veuillez réessayer",
                "js.failed": "Échec du téléchargement",
                "js.dlimg": "Télécharger l'image",
                "js.dlthumb": "Télécharger la vignette",
                "js.dlvideo": "Télécharger la vidéo",
                "js.dlaudio": "Télécharger l'audio",
                "step.1no": "Étape 1",
                "step.1title": "Copier le lien de la vidéo",
                "step.1desc": "Ouvrez YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, trouvez la vidéo à télécharger et copiez le lien complet (URL) depuis la barre d'adresse.",
                "step.1copy": "Copier le lien",
                "step.2no": "Étape 2",
                "step.2title": "Coller dans le champ",
                "step.2desc": "Revenez à la page d'accueil et collez le lien dans la zone de recherche. Toute plateforme est prise en charge et la source est détectée automatiquement.",
                "step.2paste": "Collez ici le lien de la vidéo...",
                "step.3no": "Étape 3",
                "step.3title": "Télécharger et enregistrer",
                "step.3desc": "Cliquez sur le bouton Télécharger ; une fenêtre de traitement apparaîtra. Une fois analysé, vous pouvez télécharger la vidéo, l'audio et la vignette.",
                "info.platform": "Plateformes prises en charge",
                "info.downloads": "Téléchargements",
                "d.thumb": "🖼 Vignette de la vidéo (JPG)",
                "d.video": "🎬 Vidéo HD (MP4)",
                "d.audio": "🎵 Audio séparé (M4A/WebM)",
                "tiktok.nowm": "TikTok (sans filigrane)"
            }
        },
        de: {
            name: "Deutsch",
            dict: {
                "nav.about": "Über",
                "hero.title": "Videos online herunterladen",
                "hero.subtitle": "YouTube · TikTok · Facebook · Pinterest Video-Downloader",
                "hero.placeholder": "Fügen Sie hier die Video-URL ein",
                "hero.button": "Herunterladen",
                "ad.title": "Werbung",
                "ad.sub": "Gesponsert · Ihre Anzeige hier",
                "modal.processing": "Wird verarbeitet, bitte warten...",
                "card.mp4": "MP4 herunterladen",
                "card.nowm": "Kein Wasserzeichen",
                "card.fb": "FB-Videos herunterladen",
                "card.save": "Video speichern",
                "notice.loading": "Wird geladen...",
                "js.empty": "Bitte geben Sie die Video-URL ein",
                "js.network": "Netzwerkfehler, bitte erneut versuchen",
                "js.failed": "Download fehlgeschlagen",
                "js.dlimg": "Bild herunterladen",
                "js.dlthumb": "Miniaturansicht herunterladen",
                "js.dlvideo": "Video herunterladen",
                "js.dlaudio": "Audio herunterladen",
                "step.1no": "Schritt 1",
                "step.1title": "Video-Link kopieren",
                "step.1desc": "Öffnen Sie YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, finden Sie das gewünschte Video und kopieren Sie den vollständigen Link (URL) aus der Adressleiste.",
                "step.1copy": "Link kopieren",
                "step.2no": "Schritt 2",
                "step.2title": "In das Eingabefeld einfügen",
                "step.2desc": "Kehren Sie zur Startseite zurück und fügen Sie den Link in das Suchfeld ein. Jede Plattform wird unterstützt, die Quelle wird automatisch erkannt.",
                "step.2paste": "Video-Link hier einfügen...",
                "step.3no": "Schritt 3",
                "step.3title": "Herunterladen und speichern",
                "step.3desc": "Klicken Sie auf Herunterladen; ein Verarbeitungsfenster erscheint. Nach der Analyse können Sie Video, Audio und Miniaturansicht speichern.",
                "info.platform": "Unterstützte Plattformen",
                "info.downloads": "Downloads",
                "d.thumb": "🖼 Video-Miniaturansicht (JPG)",
                "d.video": "🎬 HD-Video (MP4)",
                "d.audio": "🎵 Separates Audio (M4A/WebM)",
                "tiktok.nowm": "TikTok (ohne Wasserzeichen)"
            }
        },
        pt: {
            name: "Português",
            dict: {
                "nav.about": "Sobre",
                "hero.title": "Baixar vídeos online",
                "hero.subtitle": "Baixador de vídeos YouTube · TikTok · Facebook · Pinterest",
                "hero.placeholder": "Cole o URL do vídeo aqui",
                "hero.button": "Baixar",
                "ad.title": "Publicidade",
                "ad.sub": "Patrocinado · Seu anúncio aqui",
                "modal.processing": "Processando, aguarde...",
                "card.mp4": "Baixar MP4",
                "card.nowm": "Sem marca d'água",
                "card.fb": "Baixar vídeos do FB",
                "card.save": "Salvar vídeo",
                "notice.loading": "Carregando...",
                "js.empty": "Por favor, insira o URL do vídeo",
                "js.network": "Erro de rede, tente novamente",
                "js.failed": "Falha no download",
                "js.dlimg": "Baixar imagem",
                "js.dlthumb": "Baixar miniatura",
                "js.dlvideo": "Baixar vídeo",
                "js.dlaudio": "Baixar áudio",
                "step.1no": "Passo 1",
                "step.1title": "Copiar link do vídeo",
                "step.1desc": "Abra YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, encontre o vídeo desejado e copie o link completo (URL) da barra de endereços.",
                "step.1copy": "Copiar link",
                "step.2no": "Passo 2",
                "step.2title": "Colar na caixa de entrada",
                "step.2desc": "Volte à página inicial e cole o link na caixa de pesquisa. Qualquer plataforma é suportada e a origem é detectada automaticamente.",
                "step.2paste": "Cole aqui o link do vídeo...",
                "step.3no": "Passo 3",
                "step.3title": "Baixar e salvar",
                "step.3desc": "Clique no botão Baixar; uma janela de processamento aparecerá. Após a análise, você pode baixar vídeo, áudio e miniatura.",
                "info.platform": "Plataformas suportadas",
                "info.downloads": "Downloads",
                "d.thumb": "🖼 Miniatura do vídeo (JPG)",
                "d.video": "🎬 Vídeo HD (MP4)",
                "d.audio": "🎵 Áudio separado (M4A/WebM)",
                "tiktok.nowm": "TikTok (sem marca d'água)"
            }
        },
        ko: {
            name: "한국어",
            dict: {
                "nav.about": "정보",
                "hero.title": "온라인 동영상 다운로드",
                "hero.subtitle": "YouTube · TikTok · Facebook · Pinterest 동영상 다운로더",
                "hero.placeholder": "여기에 동영상 URL을 붙여넣으세요",
                "hero.button": "다운로드",
                "ad.title": "광고",
                "ad.sub": "스폰서 · 여기에 광고를 게재하세요",
                "modal.processing": "처리 중입니다. 잠시만 기다려 주세요...",
                "card.mp4": "MP4 다운로드",
                "card.nowm": "워터마크 없음",
                "card.fb": "FB 동영상 다운로드",
                "card.save": "동영상 저장",
                "notice.loading": "로딩 중...",
                "js.empty": "동영상 URL을 입력해 주세요",
                "js.network": "네트워크 오류, 다시 시도해 주세요",
                "js.failed": "다운로드 실패",
                "js.dlimg": "이미지 다운로드",
                "js.dlthumb": "썸네일 다운로드",
                "js.dlvideo": "동영상 다운로드",
                "js.dlaudio": "오디오 다운로드",
                "step.1no": "1단계",
                "step.1title": "동영상 링크 복사",
                "step.1desc": "YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest를 열고 다운로드할 동영상을 찾은 뒤 주소창에서 전체 링크(URL)를 복사하세요.",
                "step.1copy": "링크 복사",
                "step.2no": "2단계",
                "step.2title": "입력란에 붙여넣기",
                "step.2desc": "홈페이지로 돌아와 검색창에 링크를 붙여넣으세요. 모든 플랫폼을 지원하며 출처 웹사이트가 자동으로 인식됩니다.",
                "step.2paste": "여기에 동영상 링크를 붙여넣으세요...",
                "step.3no": "3단계",
                "step.3title": "다운로드 및 저장",
                "step.3desc": "다운로드 버튼을 클릭하면 처리 창이 나타납니다. 분석이 완료되면 동영상, 오디오, 썸네일을 저장할 수 있습니다.",
                "info.platform": "지원 플랫폼",
                "info.downloads": "다운로드 항목",
                "d.thumb": "🖼 동영상 썸네일 (JPG)",
                "d.video": "🎬 HD 동영상 (MP4)",
                "d.audio": "🎵 별도 오디오 (M4A/WebM)",
                "tiktok.nowm": "TikTok (워터마크 없음)"
            }
        },
        ja: {
            name: "日本語",
            dict: {
                "nav.about": "概要",
                "hero.title": "オンライン動画ダウンロード",
                "hero.subtitle": "YouTube · TikTok · Facebook · Pinterest 動画ダウンローダー",
                "hero.placeholder": "ここに動画のURLを貼り付けてください",
                "hero.button": "ダウンロード",
                "ad.title": "広告",
                "ad.sub": "スポンサー · あなたの広告",
                "modal.processing": "処理中です。お待ちください...",
                "card.mp4": "MP4 ダウンロード",
                "card.nowm": "透かしなし",
                "card.fb": "FB動画をダウンロード",
                "card.save": "動画を保存",
                "notice.loading": "読み込み中...",
                "js.empty": "動画のURLを入力してください",
                "js.network": "ネットワークエラー、もう一度お試しください",
                "js.failed": "ダウンロードに失敗しました",
                "js.dlimg": "画像をダウンロード",
                "js.dlthumb": "サムネイルをダウンロード",
                "js.dlvideo": "動画をダウンロード",
                "js.dlaudio": "音声をダウンロード",
                "step.1no": "ステップ1",
                "step.1title": "動画リンクをコピー",
                "step.1desc": "YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest を開き、ダウンロードしたい動画を見つけて、アドレスバーから完全なリンク（URL）をコピーします。",
                "step.1copy": "リンクをコピー",
                "step.2no": "ステップ2",
                "step.2title": "入力欄に貼り付け",
                "step.2desc": "ホームページに戻り、リンクを検索ボックスに貼り付けます。すべてのプラットフォームに対応し、元のサイトが自動的に認識されます。",
                "step.2paste": "ここに動画リンクを貼り付け...",
                "step.3no": "ステップ3",
                "step.3title": "ダウンロードして保存",
                "step.3desc": "ダウンロードボタンをクリックすると処理ウィンドウが表示されます。解析後、動画・音声・サムネイルを保存できます。",
                "info.platform": "対応プラットフォーム",
                "info.downloads": "ダウンロード内容",
                "d.thumb": "🖼 動画サムネイル（JPG）",
                "d.video": "🎬 HD動画（MP4）",
                "d.audio": "🎵 音声のみ（M4A/WebM）",
                "tiktok.nowm": "TikTok（透かしなし）"
            }
        },
        ru: {
            name: "Русский",
            dict: {
                "nav.about": "О нас",
                "hero.title": "Скачать видео онлайн",
                "hero.subtitle": "Загрузчик видео YouTube · TikTok · Facebook · Pinterest",
                "hero.placeholder": "Вставьте URL видео здесь",
                "hero.button": "Скачать",
                "ad.title": "Реклама",
                "ad.sub": "Спонсор · Ваша реклама здесь",
                "modal.processing": "Обработка, пожалуйста, подождите...",
                "card.mp4": "Скачать MP4",
                "card.nowm": "Без водяного знака",
                "card.fb": "Скачать видео FB",
                "card.save": "Сохранить видео",
                "notice.loading": "Загрузка...",
                "js.empty": "Пожалуйста, введите URL видео",
                "js.network": "Ошибка сети, попробуйте еще раз",
                "js.failed": "Ошибка загрузки",
                "js.dlimg": "Скачать изображение",
                "js.dlthumb": "Скачать миниатюру",
                "js.dlvideo": "Скачать видео",
                "js.dlaudio": "Скачать аудио",
                "step.1no": "Шаг 1",
                "step.1title": "Скопируйте ссылку на видео",
                "step.1desc": "Откройте YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, найдите нужное видео и скопируйте полную ссылку (URL) из адресной строки.",
                "step.1copy": "Скопировать ссылку",
                "step.2no": "Шаг 2",
                "step.2title": "Вставьте в поле ввода",
                "step.2desc": "Вернитесь на главную страницу и вставьте ссылку в поле поиска. Поддерживаются все платформы, источник определяется автоматически.",
                "step.2paste": "Вставьте ссылку на видео здесь...",
                "step.3no": "Шаг 3",
                "step.3title": "Скачать и сохранить",
                "step.3desc": "Нажмите кнопку «Скачать»; появится окно обработки. После анализа вы сможете сохранить видео, аудио и миниатюру.",
                "info.platform": "Поддерживаемые платформы",
                "info.downloads": "Загрузки",
                "d.thumb": "🖼 Миниатюра видео (JPG)",
                "d.video": "🎬 Видео HD (MP4)",
                "d.audio": "🎵 Отдельное аудио (M4A/WebM)",
                "tiktok.nowm": "TikTok (без водяного знака)"
            }
        },
        it: {
            name: "Italiano",
            dict: {
                "nav.about": "Informazioni",
                "hero.title": "Scarica video online",
                "hero.subtitle": "Downloader video YouTube · TikTok · Facebook · Pinterest",
                "hero.placeholder": "Incolla qui l'URL del video",
                "hero.button": "Scarica",
                "ad.title": "Pubblicità",
                "ad.sub": "Sponsorizzato · La tua pubblicità qui",
                "modal.processing": "Elaborazione, attendere prego...",
                "card.mp4": "Scarica MP4",
                "card.nowm": "Senza filigrana",
                "card.fb": "Scarica video FB",
                "card.save": "Salva video",
                "notice.loading": "Caricamento...",
                "js.empty": "Inserisci l'URL del video",
                "js.network": "Errore di rete, riprova",
                "js.failed": "Download non riuscito",
                "js.dlimg": "Scarica immagine",
                "js.dlthumb": "Scarica miniatura",
                "js.dlvideo": "Scarica video",
                "js.dlaudio": "Scarica audio",
                "step.1no": "Passo 1",
                "step.1title": "Copia il link del video",
                "step.1desc": "Apri YouTube / TikTok / Facebook / Instagram / Twitter / Pinterest, trova il video da scaricare e copia il link completo (URL) dalla barra degli indirizzi.",
                "step.1copy": "Copia link",
                "step.2no": "Passo 2",
                "step.2title": "Incolla nel campo di input",
                "step.2desc": "Torna alla home page e incolla il link nella casella di ricerca. Tutte le piattaforme sono supportate e la fonte viene rilevata automaticamente.",
                "step.2paste": "Incolla qui il link del video...",
                "step.3no": "Passo 3",
                "step.3title": "Scarica e salva",
                "step.3desc": "Fai clic sul pulsante Scarica; apparirà una finestra di elaborazione. Una volta analizzato, puoi scaricare video, audio e miniatura.",
                "info.platform": "Piattaforme supportate",
                "info.downloads": "Download",
                "d.thumb": "🖼 Miniatura del video (JPG)",
                "d.video": "🎬 Video HD (MP4)",
                "d.audio": "🎵 Audio separato (M4A/WebM)",
                "tiktok.nowm": "TikTok (senza filigrana)"
            }
        }
    };

    var FALLBACK = "en";
    var current = (function () {
        try {
            var l = localStorage.getItem("site_lang");
            return LANGS[l] ? l : FALLBACK;
        } catch (e) {
            return FALLBACK;
        }
    })();

    function t(key) {
        var d = (LANGS[current] || LANGS[FALLBACK]).dict;
        if (d[key] !== undefined) return d[key];
        if (LANGS[FALLBACK].dict[key] !== undefined) return LANGS[FALLBACK].dict[key];
        return key;
    }
    window.t = t;

    function applyI18n() {
        var els = document.querySelectorAll("[data-i18n]");
        for (var i = 0; i < els.length; i++) {
            els[i].textContent = t(els[i].getAttribute("data-i18n"));
        }
        var phs = document.querySelectorAll("[data-i18n-placeholder]");
        for (var j = 0; j < phs.length; j++) {
            phs[j].placeholder = t(phs[j].getAttribute("data-i18n-placeholder"));
        }
        var sel = document.getElementById("langSelect");
        if (sel) sel.value = current;
        document.documentElement.lang = current;
    }

    window.setLang = function (lang) {
        if (!LANGS[lang]) return;
        current = lang;
        try {
            localStorage.setItem("site_lang", lang);
        } catch (e) {}
        applyI18n();
    };

    /* 在导航 About 后注入语言切换下拉框 */
    function injectSelector() {
        var nav = document.querySelector(".nav");
        if (!nav) return;
        var about = document.querySelector('.nav a[href="/about"]');
        var sel = document.createElement("select");
        sel.id = "langSelect";
        sel.className = "lang-select";
        sel.setAttribute("aria-label", "Language");
        var codes = Object.keys(LANGS);
        for (var i = 0; i < codes.length; i++) {
            var opt = document.createElement("option");
            opt.value = codes[i];
            opt.textContent = LANGS[codes[i]].name;
            sel.appendChild(opt);
        }
        sel.value = current;
        sel.addEventListener("change", function () {
            setLang(sel.value);
        });
        if (about && about.nextSibling) {
            nav.insertBefore(sel, about.nextSibling);
        } else {
            nav.appendChild(sel);
        }
        var style = document.createElement("style");
        style.textContent =
            ".lang-select{margin-left:20px;padding:6px 10px;border:0;border-radius:6px;font-size:14px;color:#333;background:#fff;cursor:pointer;max-width:150px;}" +
            ".nav a + .lang-select{margin-left:20px;}" +
            "@media(max-width:600px){.lang-select{margin:8px 0 4px;width:100%;max-width:100%;}}";
        document.head.appendChild(style);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            injectSelector();
            applyI18n();
        });
    } else {
        injectSelector();
        applyI18n();
    }
})();
