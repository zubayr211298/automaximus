/* Automaximus: UZ / RU til almashtirgich.
 * index.html ni o'zgartirmasdan ishlaydi: sahifadagi o'zbekcha matnlarni ruscha qiladi,
 * tanlov localStorage'da saqlanadi, Telegram havolalariga til qo'shiladi (bot shu tilda ochiladi).
 * Yangi matn qo'shilsa — shu fayldagi PAIRS ro'yxatiga [uzbekcha, ruscha] juftligini qo'shing.
 */
(function () {
  'use strict';

  var STORE_KEY = 'am_lang';
  var BOT = 'automaximus_shop_bot';

  var PAIRS = [
    // sarlavha va yuqori qator
    ["Automaximus — detailing studiya va avto do'kon", "Automaximus — детейлинг-студия и автомагазин"],
    ["Bepul ko'rik", "Бесплатный осмотр"],
    ["Narx oldindan yoziladi", "Цена фиксируется заранее"],
    ["Disk va balon shu yerda", "Диски и шины — здесь же"],
    ["Narxlar", "Цены"],
    ["Detailing", "Детейлинг"],
    ["Do'kon", "Магазин"],
    ["Paketlar", "Пакеты"],
    ["Ishlarimiz", "Наши работы"],
    ["Savollar", "Вопросы"],
    ["Qo'ng'iroq", "Позвонить"],
    ["Telegramda yozish", "Написать в Telegram"],
    ["Automaximus — bosh sahifa", "Automaximus — главная"],
    ["Bo'limlar", "Разделы"],
    ["Telegram orqali yozish", "Написать в Telegram"],

    // hero
    ["Barmog'ingiz bilan surting — polirovka qiling", "Проведите пальцем — и отполируйте кузов"],
    ["Sichqonchani yurgizing — polirovka qiling", "Проведите мышью — и отполируйте кузов"],
    ["Ana, yangidek yaltiraydi! Mashinangiz ham shunday bo'ladi.", "Смотрите, блестит как новая! Ваша машина будет такой же."],
    ["Mashinangiz yangidek bo'ladi —", "Ваша машина станет как новая —"],
    ["narxi hamyonbop.", "цена по карману."],
    ["Tonirovka, broniplyonka, polirovka, ximchistka va shumoizolyatsiya. Shu yerning o'zida disk, balon va aksessuarlar do'koni ham bor. Narx ishdan oldin yozib beriladi va keyin oshmaydi.",
      "Тонировка, бронепленка, полировка, химчистка и шумоизоляция. Здесь же — магазин дисков, шин и аксессуаров. Цена фиксируется письменно до начала работ и потом не растёт."],
    ["Telegramda narxini bilish", "Узнать цену в Telegram"],
    ["Qo'ng'iroq qilish", "Позвонить"],
    ["Narx oshmaydi", "Цена не растёт"],

    // narxlar jadvali
    ["Bir tashrifda hammasi", "Всё за один визит"],
    ["Hammasi bir tashrifda", "Всё за один визит"],
    ["Tanlang — narxini aytamiz", "Выберите — назовём цену"],
    ["Tonirovka", "Тонировка"],
    ["Broniplyonka", "Бронепленка"],
    ["Polirovka", "Полировка"],
    ["Ximchistka", "Химчистка"],
    ["Shumoizolyatsiya", "Шумоизоляция"],
    ["Disk", "Диски"],
    ["Balon", "Шины"],
    ["Chexol va polik", "Чехлы и коврики"],
    ["Aksessuarlar", "Аксессуары"],
    ["modelga qarab", "в зависимости от модели"],
    ["Birga olsangiz", "Если брать вместе"],
    ["arzonroq", "дешевле"],

    // lenta
    ["Narxlar ochiq", "Цены открыты"],
    ["Yashirin to'lov yo'q", "Скрытых платежей нет"],

    // nega arzon
    ["Arzon — lekin chala emas.", "Недорого — но не «кое-как»."],
    ["Hamyonbop narx sifatni kamaytirish hisobiga emas. Qaysi xizmatni tanlamang, har bir ishga shular kiradi.",
      "Доступная цена — не за счёт качества. Какую бы услугу вы ни выбрали, в каждую работу входит следующее."],
    ["Ishdan oldin bepul ko'rik", "Бесплатный осмотр перед работой"],
    ["Narx yozib beriladi va oshmaydi", "Цена фиксируется письменно и не растёт"],
    ["Ish jarayoni rasmlari Telegramingizga", "Фото процесса работы — вам в Telegram"],
    ["Detailing, disk va balon bitta tashrifda", "Детейлинг, диски и шины — за один визит"],
    ["Toza, yopiq xonada ishlaymiz", "Работаем в чистом закрытом помещении"],
    ["Topshirishda mashinani asrash bo'yicha maslahat", "При выдаче — советы по уходу за автомобилем"],
    ["Mashinangiz uchun aniq narxni biling", "Узнайте точную цену для вашей машины"],

    // detailing xizmatlari
    ["Detailing xizmatlari", "Услуги детейлинга"],
    ["Har birini alohida yoki paket qilib olishingiz mumkin.", "Каждую услугу можно заказать отдельно или пакетом."],
    ["Yozilish", "Записаться"],
    ["Oynaga plyonka yopishtiramiz. Quyosh issig'i va zararli nuri salonga kirmaydi. Narx orqa yon oynalar va orqa oyna (sfera) uchun.",
      "Наклеиваем плёнку на стёкла. Солнечное тепло и вредные лучи не проникают в салон. Цена — за задние боковые стёкла и заднее стекло (сфера)."],
    ["Qonun ruxsat bergan darajada qoraytiramiz", "Затемняем в пределах, разрешённых законом"],
    ["Plyonka tekis yopishadi, pufakcha qolmaydi", "Плёнка ложится ровно, без пузырьков"],
    ["Ichki plastikning rangi quyoshda o'chmaydi", "Пластик салона не выгорает на солнце"],
    ["Ko'zga ko'rinmaydigan shaffof plyonka bo'yoqni tosh tegishi va tirnalishdan saqlaydi. Narx old qism uchun.",
      "Прозрачная, незаметная плёнка защищает краску от сколов и царапин. Цена — за переднюю часть."],
    ["Faqat old qismga yoki butun mashinaga", "Только на переднюю часть или на весь кузов"],
    ["Tosh tekkanidan bo'yoq ko'chmaydi", "От камней краска не откалывается"],
    ["Sotganda mashina qimmatroq ketadi", "При продаже машина стоит дороже"],
    ["Mashinani polirovka qilib, ustidan himoya qatlami suramiz. Bo'yoq yangidek yaltiraydi.",
      "Полируем кузов и наносим защитный слой. Краска блестит как новая."],
    ["Mayda tirnalish va xira joylar ketadi", "Мелкие царапины и матовые участки уходят"],
    ["Bo'yoq uzoq vaqt yaltirab turadi", "Краска долго остаётся блестящей"],
    ["Yuvish osonlashadi", "Мыть машину становится проще"],
    ["Salon qismini to'liq yuvib tozalaymiz: o'rindiqlar, shift, gilamlar va eshiklar.",
      "Полностью моем и чистим салон: сиденья, потолок, ковры и двери."],
    ["Dog'lar va yomon hid ketadi", "Пятна и неприятный запах уходят"],
    ["Ichki plastik tozalanib, rangi yangilanadi", "Пластик салона очищается, цвет обновляется"],
    ["Mashina ichi toza hid beradi", "В салоне пахнет свежестью"],
    ["Eshiklar, pol va bagajga ovoz o'tkazmaydigan maxsus qatlam yopishtiramiz. Narx 4 ta eshik uchun.",
      "Наклеиваем специальный звукоизолирующий слой на двери, пол и багажник. Цена — за 4 двери."],
    ["Yo'lda g'ildirak va shamol ovozi kam eshitiladi", "В дороге меньше слышен шум колёс и ветра"],
    ["Musiqa tiniqroq eshitiladi", "Музыка звучит чище"],
    ["Qishda salon issiqroq turadi", "Зимой в салоне теплее"],

    // do'kon
    ["Disk, balon va aksessuarlar", "Диски, шины и аксессуары"],
    ["shu yerning o'zida.", "прямо здесь."],
    ["Detailingga kelganingizda yangi disk yoki balonni ham tanlab, o'rnatib beramiz. Boshqa joyga borish shart emas.",
      "Приезжайте на детейлинг — заодно выберете новые диски или шины, и мы их установим. Ехать в другое место не нужно."],
    ["Modelingizga mosini so'rash", "Узнать, что подойдёт к вашей модели"],
    ["Litoy va shtamp disklar, turli diametr va rangda. O'rnatib beramiz.", "Литые и штампованные диски разных диаметров и цветов. Установим."],
    ["Narxini so'rash", "Узнать цену"],
    ["Yozgi va qishki balonlar. Almashtirish va o'rnatish shu yerda.", "Летние и зимние шины. Замена и установка — здесь же."],
    ["Modelingizga mos chexollar (450 000 so'mdan) va 3D poliklar (200 000 so'mdan).", "Чехлы под вашу модель (от 450 000 сум) и 3D-коврики (от 200 000 сум)."],
    ["Mashinangiz uchun kerakli aksessuarlar va elektrik xizmati.", "Нужные аксессуары для вашей машины и услуги автоэлектрика."],
    ["Mashina rusumi va o'lchamni yozing (masalan,", "Напишите марку машины и размер (например,"],
    ["). Mos variantlarni rasm va narxi bilan yuboramiz.", "). Мы пришлём подходящие варианты с фото и ценами."],

    // paketlar
    ["Paket olsangiz — arzonroq.", "В пакете — дешевле."],
    ["Xizmatlarni, hatto disk bilan birga, bitta tashrifda olsangiz, alohida olgandan ko'ra kamroq to'laysiz.",
      "Если заказать услуги (даже вместе с дисками) за один визит, вы заплатите меньше, чем по отдельности."],
    ["Start", "Старт"],
    ["Har kuni haydaydiganlar uchun", "Для тех, кто ездит каждый день"],
    ["Odatiy narx:", "Обычная цена:"],
    ["Tejaysiz:", "Экономия:"],
    ["Salon ximchistkasi", "Химчистка салона"],
    ["Shu paketni tanlash", "Выбрать этот пакет"],
    ["Eng ko'p tanlanadi", "Самый популярный"],
    ["Optimal", "Оптимальный"],
    ["Yangi olingan mashina uchun", "Для новой машины"],
    ["Old qismga broniplyonka", "Бронепленка на переднюю часть"],
    ["To'liq", "Полный"],
    ["Disk + yaltiroq", "Диски + блеск"],
    ["Yangi disk olayotganlar uchun", "Для тех, кто покупает новые диски"],
    ["600 000 so'm + fara polirovkasi bepul", "600 000 сум + бесплатная полировка фар"],
    ["Disk komplekti (o'rnatish bilan)", "Комплект дисков (с установкой)"],
    ["Fara polirovkasi", "Полировка фар"],
    ["Aniq narx mashina turiga qarab ko'rikda aytiladi.", "Точная цена называется на осмотре и зависит от типа машины."],

    // qanday ishlaymiz
    ["Qanday ishlaymiz", "Как мы работаем"],
    ["To'rt oddiy qadam. Kutilmagan narsa yo'q.", "Четыре простых шага. Никаких сюрпризов."],
    ["Usta mashinangizni ko'rib, nima kerakligini tushuntiradi.", "Мастер осматривает машину и объясняет, что нужно сделать."],
    ["Narxni kelishamiz", "Согласовываем цену"],
    ["Narx va muddatni yozib beramiz. Keyin narx oshmaydi.", "Фиксируем цену и сроки письменно. Потом цена не растёт."],
    ["Ishni bajaramiz", "Выполняем работу"],
    ["Toza xonada ishlaymiz, jarayon rasmlarini Telegramga yuboramiz.", "Работаем в чистом помещении, фото процесса присылаем в Telegram."],
    ["Topshiramiz", "Выдаём машину"],
    ["Natijani birga ko'ramiz va mashinani asrash bo'yicha maslahat beramiz.", "Вместе смотрим результат и даём советы по уходу за автомобилем."],

    // ishlarimiz
    ["Farg'onadagi studiyamizda tayyorlangan mashinalar. Bosing — Instagram'da videosini ko'rasiz.", "Машины, подготовленные в нашей студии в Фергане. Нажмите — видео смотрите в Instagram."],
    ["Videoni ko'rish", "Смотреть видео"],
    ["Tonirovka va balon", "Тонировка и шины"],
    ["To'liq shumoizolyatsiya", "Полная шумоизоляция"],
    ["Kompleks tayyorlash", "Комплексная подготовка"],
    ["Yangi mashinaga barcha ishlar", "Все работы для новой машины"],
    ["Yangi disk o'rnatildi", "Установлены новые диски"],
    ["Shumoizolyatsiya va salon", "Шумоизоляция и салон"],

    // savol-javob
    ["Ko'p beriladigan savollar", "Частые вопросы"],
    ["Ish qancha vaqt oladi?", "Сколько времени занимает работа?"],
    ["Xizmatga bog'liq: tonirovka va ximchistka odatda bir kunda, broniplyonka va shumoizolyatsiya bir necha kunda tayyor bo'ladi. Aniq muddatni ko'rikda aytamiz.",
      "Зависит от услуги: тонировка и химчистка обычно делаются за один день, бронепленка и шумоизоляция — за несколько дней. Точный срок назовём на осмотре."],
    ["Narx nimaga qarab belgilanadi?", "От чего зависит цена?"],
    ["Mashina kattaligi, bo'yoq holati va tanlangan materialga qarab. Narxni ko'rikda yozib beramiz va keyin u oshmaydi.",
      "От размера машины, состояния краски и выбранного материала. Цену фиксируем письменно на осмотре, и потом она не растёт."],
    ["Tonirovka qonunga mosmi?", "Тонировка соответствует закону?"],
    ["Ha. Faqat qonun ruxsat bergan darajada qoraytiramiz va buni oldindan tushuntirib beramiz.", "Да. Затемняем только в пределах, разрешённых законом, и заранее это объясняем."],
    ["Broniplyonka bo'yoqqa zarar bermaydimi?", "Бронепленка не вредит краске?"],
    ["Yo'q. Sifatli plyonka bo'yoqni faqat himoya qiladi. Kerak bo'lsa, uni iz qoldirmasdan olib tashlash mumkin.", "Нет. Качественная плёнка только защищает краску. При необходимости её можно снять без следов."],
    ["Disk va balonni o'rnatib berasizmi?", "Вы устанавливаете диски и шины?"],
    ["Ha. Disk va balonni shu yerning o'zida o'rnatib beramiz. Mashina rusumi va o'lchamni Telegramga yozsangiz, mos variantlarni rasm va narxi bilan yuboramiz.",
      "Да. Диски и шины устанавливаем прямо здесь. Напишите в Telegram марку машины и размер — пришлём подходящие варианты с фото и ценами."],

    // yozilish bo'limi va forma
    ["Narxni 1 daqiqada bilib oling.", "Узнайте цену за 1 минуту."],
    ["Telegram botimizga mashinangiz rusumini va nima kerakligini yozing. Narx va bo'sh vaqtni aytamiz. Bepul, hech narsaga majburlamaydi.",
      "Напишите нашему Telegram-боту марку машины и что нужно сделать. Назовём цену и свободное время. Бесплатно, ни к чему не обязывает."],
    ["Farg'ona, Al Farg'oniy ko'chasi, 108", "Фергана, ул. Аль-Фаргони, 108"],
    ["— xaritada ochish", "— открыть на карте"],
    ["Yoki raqamingizni qoldiring, o'zimiz qo'ng'iroq qilamiz", "Или оставьте номер — мы сами позвоним"],
    ["Qaysi xizmat kerak?", "Какая услуга нужна?"],
    ["Ismingiz", "Ваше имя"],
    ["Telefon raqam", "Номер телефона"],
    ["Mashina rusumi", "Марка машины"],
    ["(ixtiyoriy)", "(по желанию)"],
    ["Bu maydonni bo'sh qoldiring", "Оставьте это поле пустым"],
    ["Narxni bilish — bepul", "Узнать цену — бесплатно"],
    ["Yuborilmoqda…", "Отправляем…"],
    ["Raqamingiz faqat qo'ng'iroq uchun ishlatiladi.", "Ваш номер используется только для звонка."],
    ["Masalan, Jasur", "Например, Жасур"],
    ["Masalan, Chevrolet Cobalt", "Например, Chevrolet Cobalt"],
    ["Rahmat! So'rovingiz qabul qilindi.", "Спасибо! Ваша заявка принята."],
    ["Yangi so'rov", "Новая заявка"],
    ["Tanlangan xizmatlar:", "Выбранные услуги:"],
    ["ko'rikda aniqlanadi", "определим на осмотре"],
    [". Tez orada qo'ng'iroq qilamiz.", ". Скоро мы вам позвоним."],
    ["So'rovni yuborib bo'lmadi. Iltimos,", "Не удалось отправить заявку. Пожалуйста,"],
    ["Telegramda yozing", "напишите в Telegram"],
    ["yoki qo'ng'iroq qiling:", "или позвоните:"],

    // pastki qism
    ["© Automaximus · Detailing studiya va avto do'kon · Farg'ona, Al Farg'oniy ko'chasi, 108", "© Automaximus · Детейлинг-студия и автомагазин · Фергана, ул. Аль-Фаргони, 108"],
    ["Telegramda narx", "Цена в Telegram"],

    // rasm tavsiflari (alt)
    ["Usta oq avtomobil oynasiga tonirovka plyonkasini rakel bilan yopishtirmoqda", "Мастер клеит тонировочную плёнку на стекло белого автомобиля"],
    ["Usta qora avtomobil kapotiga broniplyonkani rakel bilan yopishtirmoqda", "Мастер клеит бронепленку на капот чёрного автомобиля"],
    ["Qora avtomobil kapoti polirovka mashinasi bilan yaltiratilmoqda", "Капот чёрного автомобиля полируется машинкой"],
    ["Kulrang mato o'rindiq ekstraktor bilan tozalanmoqda", "Серое тканевое сиденье чистится экстрактором"],
    ["Eshik ichiga shumoizolyatsiya qatlami yopishtirilmoqda", "Внутрь двери клеится слой шумоизоляции"],
    ["Qizil supportli qora litoy disk", "Чёрный литой диск с красным суппортом"],
    ["Do'kon javonida yangi balonlar", "Новые шины на полке магазина"],
    ["Qizil chokli qora eko-charm chexol va 3D polik", "Чёрный чехол из экокожи с красной строчкой и 3D-коврик"],
    ["Telefon ushlagich, videoregistrator, rul g'ilofi va boshqa aksessuarlar", "Держатель для телефона, видеорегистратор, чехол на руль и другие аксессуары"]
  ];

  var RULES = [
    [/^([\d ]+) so'mdan$/, function (m) { return 'от ' + m[1] + ' сум'; }],
    [/^([\d ]+) so'm$/, function (m) { return m[1] + ' сум'; }],
    [/^([\d,]+) soat$/, function (m) {
      var n = m[1];
      if (n.indexOf(',') !== -1) { return n + ' часа'; }
      var k = parseInt(n, 10), r10 = k % 10, r100 = k % 100;
      if (r10 === 1 && r100 !== 11) { return n + ' час'; }
      if (r10 >= 2 && r10 <= 4 && (r100 < 12 || r100 > 14)) { return n + ' часа'; }
      return n + ' часов';
    }],
    [/^Ish vaqti: (.+)$/, function (m) { return 'Время работы: ' + m[1]; }]
  ];

  var norm = function (s) {
    return String(s).replace(/[‘’ʻʼ`´]/g, "'").replace(/\s+/g, ' ').trim();
  };

  var DICT = {};
  PAIRS.forEach(function (p) { DICT[norm(p[0])] = p[1]; });

  var lookup = function (core) {
    if (Object.prototype.hasOwnProperty.call(DICT, core)) { return DICT[core]; }
    var i, m;
    for (i = 0; i < RULES.length; i++) {
      m = core.match(RULES[i][0]);
      if (m) { return RULES[i][1](m); }
    }
    // "Tonirovka, Polirovka" kabi ro'yxat
    if (core.indexOf(', ') !== -1) {
      var parts = core.split(', '), out = [];
      for (i = 0; i < parts.length; i++) {
        var one = lookup(parts[i]);
        if (one === null) { return null; }
        out.push(one);
      }
      return out.join(', ');
    }
    // alt: "BYD Chazor — Tonirovka va balon, Automaximus ishi"
    m = core.match(/^(.+?) — (.+), Automaximus ishi$/);
    if (m) {
      var svc = lookup(m[2]);
      if (svc !== null) { return m[1] + ' — ' + svc + ', работа Automaximus'; }
    }
    return null;
  };

  var tr = function (text) {
    var core = norm(text);
    if (!core) { return text; }
    var out = lookup(core);
    if (out === null) { return text; }
    return text.match(/^\s*/)[0] + out + text.match(/\s*$/)[0];
  };

  // ---------- til holati ----------
  var readStored = function () { try { return localStorage.getItem(STORE_KEY); } catch (e) { return null; } };
  var fromUrl = function () {
    try { return new URLSearchParams(window.location.search).get('lang'); } catch (e) { return null; }
  };
  var valid = function (l) { return l === 'uz' || l === 'ru' ? l : null; };

  var explicit = !!(valid(fromUrl()) || valid(readStored()));
  var lang = valid(fromUrl()) || valid(readStored()) || 'uz';
  if (valid(fromUrl())) { try { localStorage.setItem(STORE_KEY, lang); } catch (e) {} }

  var ATTRS = ['placeholder', 'alt', 'aria-label', 'title'];
  var textRec = new WeakMap();
  var attrRec = new WeakMap();
  var titleUz = null;

  var skipped = function (el) { return !!(el && el.closest && el.closest('script,style,[data-i18n-skip]')); };

  var processText = function (node) {
    if (skipped(node.parentElement)) { return; }
    var v = node.nodeValue, rec = textRec.get(node);
    if (!rec) { rec = { orig: v, applied: v }; textRec.set(node, rec); }
    else if (v !== rec.applied) { rec.orig = v; rec.applied = v; }
    var want = lang === 'ru' ? tr(rec.orig) : rec.orig;
    if (want !== v) { node.nodeValue = want; }
    rec.applied = want;
  };

  var processAttr = function (el, name) {
    if (skipped(el)) { return; }
    var v = el.getAttribute(name);
    if (v === null) { return; }
    var recs = attrRec.get(el);
    if (!recs) { recs = {}; attrRec.set(el, recs); }
    var rec = recs[name];
    if (!rec) { rec = recs[name] = { orig: v, applied: v }; }
    else if (v !== rec.applied) { rec.orig = v; rec.applied = v; }
    var want = lang === 'ru' ? tr(rec.orig) : rec.orig;
    if (want !== v) { el.setAttribute(name, want); }
    rec.applied = want;
  };

  var processHref = function (a) {
    if (!explicit) { return; }
    var href = a.getAttribute('href');
    if (!href || href.indexOf('https://t.me/' + BOT) !== 0) { return; }
    try {
      var u = new URL(href), s = u.searchParams.get('start');
      if (s === null) { return; }
      u.searchParams.set('start', s.replace(/__(uz|ru)$/, '') + '__' + lang);
      var next = u.toString();
      if (next !== href) { a.setAttribute('href', next); }
    } catch (e) {}
  };

  var processTree = function (root) {
    if (root.nodeType === 3) { processText(root); return; }
    if (root.nodeType !== 1 || skipped(root)) { return; }
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), n;
    while ((n = w.nextNode())) { processText(n); }
    var els = [root].concat([].slice.call(root.querySelectorAll('*')));
    els.forEach(function (el) {
      ATTRS.forEach(function (a) { if (el.hasAttribute(a)) { processAttr(el, a); } });
      if (el.tagName === 'A') { processHref(el); }
    });
  };

  var processTitle = function () {
    if (titleUz === null) { titleUz = document.title; }
    document.title = lang === 'ru' ? tr(titleUz) : titleUz;
    document.documentElement.setAttribute('lang', lang);
  };

  // ---------- almashtirgich tugmasi ----------
  var injectStyle = function () {
    if (document.getElementById('i18n-style')) { return; }
    var st = document.createElement('style');
    st.id = 'i18n-style';
    st.textContent =
      '.lsw{display:inline-flex;flex:none;border:1.5px solid #CFCFCF;border-radius:10px;overflow:hidden;background:#FFFFFF}' +
      '.lsw button{min-height:44px;min-width:48px;padding:0 12px;border:0;background:#FFFFFF;color:#141414;font:700 14px/1 inherit;letter-spacing:.04em;cursor:pointer}' +
      '.lsw button[aria-pressed="true"]{background:#D7182A;color:#FFFFFF}' +
      '.lsw button:focus-visible{outline:3px solid #141414;outline-offset:-3px}' +
      // telefonda logo + tugma ekranga sig'sin (aks holda UZ|RU o'ng chetdan kesilib qoladi)
      '@media (max-width:760px){header nav{gap:8px !important}header nav>a:first-child{min-width:0}' +
      '.navlogo{height:auto !important;width:min(293px,calc(100vw - 150px)) !important}' +
      '.lsw button{min-width:40px;padding:0 8px}' +
      // narxlar jadvali telefonda ekran kengligiga sig'sin (qatorlar o'ralsin, o'ng chetdan kesilmasin)
      '.hero-in>*{min-width:0;max-width:100%}.board-cols>*{min-width:0}' +
      '.brow{flex-wrap:wrap;column-gap:12px;row-gap:2px}.brow>span:first-child{min-width:0}' +
      '.brow .price{white-space:normal;margin-left:auto;text-align:right}}';
    document.head.appendChild(st);
  };

  var syncButtons = function () {
    var box = document.getElementById('lang-switch');
    if (!box) { return; }
    [].forEach.call(box.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true' : 'false');
    });
  };

  var setLang = function (l) {
    if (!valid(l) || l === lang) { return; }
    lang = l;
    explicit = true;
    try { localStorage.setItem(STORE_KEY, lang); } catch (e) {}
    processTitle();
    processTree(document.body);
    syncButtons();
  };

  var inject = function () {
    if (document.getElementById('lang-switch')) { return true; }
    var nav = document.querySelector('header nav');
    var host = nav && nav.lastElementChild;
    if (!host) { return false; }
    injectStyle();
    var box = document.createElement('div');
    box.id = 'lang-switch';
    box.className = 'lsw';
    box.setAttribute('data-i18n-skip', '');
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', 'Til / Язык');
    ['uz', 'ru'].forEach(function (l) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-lang', l);
      b.textContent = l.toUpperCase();
      b.addEventListener('click', function () { setLang(l); });
      box.appendChild(b);
    });
    host.appendChild(box);
    syncButtons();
    return true;
  };

  // ---------- kuzatuvchi: React yangilasa ham tarjima saqlanadi ----------
  var observer = new MutationObserver(function (records) {
    inject();
    records.forEach(function (r) {
      if (r.type === 'characterData') { processText(r.target); }
      else if (r.type === 'attributes') {
        if (r.attributeName === 'href') { if (r.target.tagName === 'A') { processHref(r.target); } }
        else { processAttr(r.target, r.attributeName); }
      } else {
        [].forEach.call(r.addedNodes, function (n) { processTree(n); });
      }
    });
    observer.takeRecords();
  });

  var start = function () {
    inject();
    processTitle();
    processTree(document.body);
    observer.observe(document.body, {
      subtree: true, childList: true, characterData: true,
      attributes: true, attributeFilter: ATTRS.concat(['href'])
    });
  };

  // tekshirish uchun: tarjimasiz qolgan o'zbekcha matnlar ro'yxati
  window.__i18nMissing = function () {
    var out = [], w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n;
    while ((n = w.nextNode())) {
      var rec = textRec.get(n);
      if (!rec || skipped(n.parentElement)) { continue; }
      var core = norm(rec.orig);
      if (core && /[A-Za-z]{3,}/.test(core) && tr(rec.orig) === rec.orig) { out.push(core); }
    }
    return out;
  };
  window.__setLang = setLang;

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start); } else { start(); }
})();
