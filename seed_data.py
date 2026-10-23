"""Course plan and authentic, public-domain seed texts.

The seed catalogue is deliberately small enough to ship with the app, but it
contains multiple authentic texts for each major unit. Instructors can extend
it through the in-app importer without changing the code.
"""

COURSE_PLAN = [
    {
        "week": 1,
        "title": "Introduction to Literary Translation",
        "focus": "Translation as interpretation; the translator's role; diagnostic work.",
        "activities": "Compare alternative translations and establish a translation journal.",
        "output": "Diagnostic translation and learning goals",
    },
    {
        "week": 2,
        "title": "Close Reading and the Translation Brief",
        "focus": "Genre, audience, purpose, tone, register, context, and authorial intention.",
        "activities": "Annotate an authentic source text and write a translation brief.",
        "output": "Annotated source text and translation brief",
    },
    {
        "week": 3,
        "title": "Style, Voice, and Register",
        "focus": "Diction, syntax, repetition, rhythm, narrative voice, and stylistic consistency.",
        "activities": "Produce and compare alternative prose versions.",
        "output": "Annotated prose translation",
    },
    {
        "week": 4,
        "title": "Poetry I: Imagery and Figurative Language",
        "focus": "Metaphor, simile, symbolism, ambiguity, and culturally embedded imagery.",
        "activities": "Translate and discuss figurative language in authentic poems.",
        "output": "Poetry translation and translator's note",
    },
    {
        "week": 5,
        "title": "Poetry II: Form, Rhythm, and Sound",
        "focus": "Rhyme, rhythm, lineation, sound patterns, and formal versus semantic equivalence.",
        "activities": "Create two versions of a poem and justify formal choices.",
        "output": "Two alternative versions of a poem",
    },
    {
        "week": 6,
        "title": "Fiction I: Narrative Voice and Focalization",
        "focus": "Point of view, tense, free indirect discourse, cohesion, and narrative distance.",
        "activities": "Translate a prose extract while tracking voice and viewpoint.",
        "output": "Prose translation of approximately 400 words",
    },
    {
        "week": 7,
        "title": "Fiction II: Dialogue, Dialect, and Characterisation",
        "focus": "Speech patterns, sociolect, idiom, names, cultural references, and character voice.",
        "activities": "Translate dialogue and test it through reading aloud.",
        "output": "Dialogue translation and strategy memo",
    },
    {
        "week": 8,
        "title": "Midterm Translation Workshop",
        "focus": "Drafting, peer review, translation rubrics, and individual feedback.",
        "activities": "Workshop a substantial translation and its critical commentary.",
        "output": "Midterm translation project with commentary",
    },
    {
        "week": 9,
        "title": "Drama and Performability",
        "focus": "Dialogue, subtext, stage directions, spoken language, and performance considerations.",
        "activities": "Translate and perform a short dramatic scene.",
        "output": "Translation of a dramatic scene",
    },
    {
        "week": 10,
        "title": "Culture, Ideology, and Ethics",
        "focus": "Domestication, foreignisation, representation, gender, religion, and colonial contexts.",
        "activities": "Compare strategies for culturally and ideologically marked passages.",
        "output": "Critical reflection on cultural choices",
    },
    {
        "week": 11,
        "title": "Humour, Wordplay, Allusion, and Intertextuality",
        "focus": "Untranslatability, adaptation, compensation, and creative reformulation.",
        "activities": "Develop and evaluate alternative solutions to challenging passages.",
        "output": "Annotated translation of a challenging passage",
    },
    {
        "week": 12,
        "title": "Revision and Translation Quality Assessment",
        "focus": "Self-editing, peer editing, coherence, style, accuracy, and naturalness.",
        "activities": "Revise a translation with a transparent revision log.",
        "output": "Revised translation and revision log",
    },
    {
        "week": 13,
        "title": "Translation Technology and Final Portfolio Development",
        "focus": "Critical use of CAT tools, machine translation, generative AI, authorship, and bias.",
        "activities": "Compare human and AI suggestions and prepare the final portfolio.",
        "output": "Final portfolio draft and technology-use statement",
    },
    {
        "week": 14,
        "title": "Final Presentations and Course Synthesis",
        "focus": "Explaining translation choices and reflecting on professional practice.",
        "activities": "Present a portfolio extract and discuss its translation decisions.",
        "output": "Final portfolio and reflective commentary",
    },
]


SEED_TEXTS = [
    {
        "title": "Sonnet 18",
        "author": "William Shakespeare",
        "year": "1609",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Poetry",
        "week": 4,
        "difficulty": "Advanced",
        "themes": "time; beauty; mortality; metaphor",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://en.wikisource.org/wiki/Shakespeare%27s_Sonnets",
        "text": """Shall I compare thee to a summer's day?
Thou art more lovely and more temperate:
Rough winds do shake the darling buds of May,
And summer's lease hath all too short a date;
Sometime too hot the eye of heaven shines,
And often is his gold complexion dimm'd;
And every fair from fair sometime declines,
By chance, or nature's changing course, untrimm'd;
But thy eternal summer shall not fade,
Nor lose possession of that fair thou ow'st;
Nor shall death brag thou wander'st in his shade,
When in eternal lines to time thou grow'st:
So long as men can breathe or eyes can see,
So long lives this, and this gives life to thee.""",
    },
    {
        "title": "Pride and Prejudice: Opening",
        "author": "Jane Austen",
        "year": "1813",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 6,
        "difficulty": "Intermediate",
        "themes": "irony; society; marriage; narrative voice",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://www.gutenberg.org/ebooks/1342",
        "text": """It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.

However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters.""",
    },
    {
        "title": "A Tale of Two Cities: Opening",
        "author": "Charles Dickens",
        "year": "1859",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 3,
        "difficulty": "Advanced",
        "themes": "paradox; history; society; rhythm",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://www.gutenberg.org/ebooks/98",
        "text": """It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way.""",
    },
    {
        "title": "The Raven: Opening Stanza",
        "author": "Edgar Allan Poe",
        "year": "1845",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Poetry",
        "week": 5,
        "difficulty": "Advanced",
        "themes": "sound; grief; repetition; atmosphere",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://en.wikisource.org/wiki/The_Raven",
        "text": """Once upon a midnight dreary, while I pondered, weak and weary,
Over many a quaint and curious volume of forgotten lore—
While I nodded, nearly napping, suddenly there came a tapping,
As of some one gently rapping, rapping at my chamber door.
\"'Tis some visitor,\" I muttered, \"tapping at my chamber door—
Only this and nothing more.\"""",
    },
    {
        "title": "Alice's Adventures in Wonderland: Opening",
        "author": "Lewis Carroll",
        "year": "1865",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 2,
        "difficulty": "Intermediate",
        "themes": "childhood; perspective; dialogue; irony",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://www.gutenberg.org/ebooks/11",
        "text": """Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, \"and what is the use of a book,\" thought Alice \"without pictures or conversations?\"""",
    },
    {
        "title": "The Happy Prince: Opening",
        "author": "Oscar Wilde",
        "year": "1888",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 10,
        "difficulty": "Intermediate",
        "themes": "appearance; compassion; symbolism",
        "rights": "Public-domain source text in some jurisdictions; verify local rules.",
        "source_url": "https://www.gutenberg.org/ebooks/902",
        "text": """High above the city, on a tall column, stood the statue of the Happy Prince. He was gilded all over with thin leaves of fine gold, for eyes he had two bright sapphires, and a large red ruby glowed on his sword-hilt.""",
    },
    {
        "title": "Frankenstein: Family and Memory",
        "author": "Mary Shelley",
        "year": "1818",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 6,
        "difficulty": "Advanced",
        "themes": "memory; identity; family; narration",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://www.gutenberg.org/ebooks/84",
        "text": """I am by birth a Genevese; and my family is one of the most distinguished of that republic. My ancestors had been for many generations counsellors and syndics; and my father had filled several public situations with honour and reputation.""",
    },
    {
        "title": "Treasure Island: The Commission",
        "author": "Robert Louis Stevenson",
        "year": "1883",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Fiction",
        "week": 7,
        "difficulty": "Intermediate",
        "themes": "voice; adventure; testimony; narrative frame",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://www.gutenberg.org/ebooks/120",
        "text": """The squire, and Dr. Livesey, and the rest of these gentlemen, having asked me to write down the whole particulars about Treasure Island, from the beginning to the end, keeping nothing back but the bearings of the island, and that only because there is still treasure not yet lifted, I take up my pen in the year of grace 17— and go back to the time when my father kept the Admiral Benbow inn.""",
    },
    {
        "title": "Remember",
        "author": "Christina Rossetti",
        "year": "1862",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Poetry",
        "week": 5,
        "difficulty": "Advanced",
        "themes": "memory; separation; form; consolation",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://en.wikisource.org/wiki/Sonnets_(Rossetti)/Remember",
        "text": """Remember me when I am gone away,
Gone far away into the silent land;
When you can no more hold me by the hand,
Nor I half turn to go yet turning stay.
Remember me when no more day by day
You tell me of our future that you planned:
Only remember me; you understand
It will be late to counsel then or pray.""",
    },
    {
        "title": "Song of Myself: Opening",
        "author": "Walt Whitman",
        "year": "1855",
        "language": "English",
        "direction": "English → Arabic",
        "genre": "Poetry",
        "week": 4,
        "difficulty": "Advanced",
        "themes": "self; body; democracy; free verse",
        "rights": "Public-domain source text; verify local redistribution rules.",
        "source_url": "https://en.wikisource.org/wiki/Leaves_of_Grass_(1892)/Song_of_Myself",
        "text": """I celebrate myself, and sing myself,
And what I assume you shall assume,
For every atom belonging to me as good belongs to you.

I loafe and invite my soul,
I lean and loafe at my ease observing a spear of summer grass.""",
    },
    {
        "title": "معلقة امرئ القيس: الوقوف على الأطلال",
        "author": "امرؤ القيس",
        "year": "نحو القرن السادس الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 4,
        "difficulty": "Advanced",
        "themes": "memory; place; absence; imagery",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """قِفا نَبكِ مِن ذِكرى حَبيبٍ وَمَنزلِ
بِسِقطِ اللِوى بَينَ الدَخولِ فَحَومَلِ
فَتوضِحَ فَالمِقراةِ لَم يَعفُ رَسمُها
لِما نَسَجَتها مِن جَنوبٍ وَشَمأَلِ""",
    },
    {
        "title": "على قدر أهل العزم",
        "author": "المتنبي",
        "year": "نحو القرن العاشر الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 5,
        "difficulty": "Advanced",
        "themes": "ambition; heroism; proportion; antithesis",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """على قدرِ أهلِ العزمِ تأتي العزائمُ
وتأتي على قدرِ الكرامِ المكارمُ
وتعظمُ في عينِ الصغيرِ صغارُها
وتصغرُ في عينِ العظيمِ العظائمُ""",
    },
    {
        "title": "السيف أصدق أنباء من الكتب",
        "author": "أبو تمام",
        "year": "نحو القرن التاسع الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 10,
        "difficulty": "Advanced",
        "themes": "war; knowledge; rhetoric; contrast",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """السيفُ أصدقُ أنباءً من الكتبِ
في حدِّه الحدُّ بين الجدِّ واللعبِ
بيضُ الصفائحِ لا سودُ الصحائفِ في
متونِهنَّ جلاءُ الشكِّ والريبِ""",
    },
    {
        "title": "هل غادر الشعراء من متردم",
        "author": "عنترة بن شداد",
        "year": "نحو القرن السادس الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 3,
        "difficulty": "Advanced",
        "themes": "tradition; place; address; heroic voice",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """هل غادرَ الشعراءُ من متردَّمِ
أم هل عرفتَ الدارَ بعدَ توهُّمِ
يا دارَ عبلةَ بالجواءِ تكلَّمي
وعِمي صباحاً دارَ عبلةَ واسلمي""",
    },
    {
        "title": "يذكرني طلوع الشمس صخراً",
        "author": "الخنساء",
        "year": "نحو القرن السابع الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 4,
        "difficulty": "Intermediate",
        "themes": "mourning; memory; repetition; grief",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """يذكِّرني طلوعُ الشمسِ صخراً
وأذكرُهُ لكلِّ غروبِ شمسِ
ولولا كثرةُ الباكينَ حولي
على إخوانِهم لقتلتُ نفسي""",
    },
    {
        "title": "غير مجد في ملتي واعتقادي",
        "author": "أبو العلاء المعري",
        "year": "نحو القرن الحادي عشر الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 11,
        "difficulty": "Advanced",
        "themes": "mourning; belief; sound; paradox",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """غيرُ مُجدٍ في ملَّتي واعتقادي
نوحُ باكٍ ولا ترنُّمُ شادِ
وشبيهٌ صوتُ النعيِّ إذا قيسَ
بصوتِ البشيرِ في كلِّ نادِ""",
    },
    {
        "title": "أضحى التنائي بديلاً من تدانينا",
        "author": "ابن زيدون",
        "year": "نحو القرن الحادي عشر الميلادي",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Poetry",
        "week": 5,
        "difficulty": "Advanced",
        "themes": "separation; love; sound; parallelism",
        "rights": "Classical public-domain source; consult a scholarly edition for teaching.",
        "source_url": "https://ar.wikisource.org/",
        "text": """أضحى التنائي بديلاً من تدانينا
ونابَ عن طيبِ لقيانا تجافينا
ألا وقد حانَ صبحُ البينِ صبحُنا
حينٌ فقامَ بنا للحينِ ناعينا""",
    },
    {
        "title": "مدخل من الحكاية الإطارية",
        "author": "ألف ليلة وليلة (تراث سردي)",
        "year": "تراث متداول",
        "language": "Arabic",
        "direction": "Arabic → English",
        "genre": "Fiction",
        "week": 6,
        "difficulty": "Intermediate",
        "themes": "frame narrative; address; storytelling; formula",
        "rights": "Traditional public-domain narrative formula; use a verified scholarly edition.",
        "source_url": "https://ar.wikisource.org/wiki/%D8%A3%D9%84%D9%81_%D9%84%D9%8A%D9%84%D8%A9_%D9%88%D9%84%D9%8A%D9%84%D8%A9/%D8%A7%D9%84%D8%B3%D9%86%D8%AF%D8%A8%D8%A7%D8%AF_%D8%A7%D9%84%D8%A8%D8%AD%D8%B1%D9%8A",
        "text": """قالت: بلغني أيها الملك السعيد أن السندباد البحري لما ذهب مع الشيخ إلى شاطئ البحر ورأى الفلك الذي جاء فيه من خشب الصندل.""",
    },
]

