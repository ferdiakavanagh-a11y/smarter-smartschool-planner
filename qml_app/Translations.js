.pragma library

// UI labels only; school and user content pass through unchanged.
var pairs = [
  [
    "File preview",
    "Bestandsvoorbeeld"
  ],
  [
    "Showing the first 256 KB. Save the original for the complete file.",
    "De eerste 256 KB worden getoond. Bewaar het origineel voor het volledige bestand."
  ],
  [
    "Saved on this computer",
    "Bewaard op deze computer"
  ],
  [
    "Save as",
    "Opslaan als"
  ],
  [
    "Image",
    "Afbeelding"
  ],
  [
    "This image could not be opened.",
    "Deze afbeelding kon niet worden geopend."
  ],
  [
    "Text document",
    "Tekstdocument"
  ],
  [
    "Focus",
    "Focus"
  ],
  [
    "Minimize",
    "Minimaliseren"
  ],
  [
    "STOPWATCH",
    "STOPWATCH"
  ],
  [
    "PAUSED",
    "GEPAUZEERD"
  ],
  [
    "Elapsed focus time ",
    "Verstreken focustijd "
  ],
  [
    "INSTRUCTIONS",
    "INSTRUCTIES"
  ],
  [
    "No additional instructions.",
    "Verder hoef je niets te doen."
  ],
  [
    "Review the topic, record your working and bring one question to class.",
    "Herhaal het onderwerp, noteer je uitwerking en neem één vraag mee naar de les."
  ],
  [
    "Synthetic task · memory only",
    "Voorbeeldtaak · alleen in het geheugen"
  ],
  [
    "Focus controls",
    "Focusbediening"
  ],
  [
    "Pause",
    "Pauzeren"
  ],
  [
    "Resume",
    "Hervatten"
  ],
  [
    "On top",
    "Altijd bovenaan"
  ],
  [
    "Done",
    "Klaar"
  ],
  [
    "Complete",
    "Voltooien"
  ],
  [
    "Exit",
    "Afsluiten"
  ],
  [
    " missed",
    " gemist"
  ],
  [
    " unread",
    " ongelezen"
  ],
  [
    ", unread",
    ", ongelezen"
  ],
  [
    "Student follow-up",
    "Leerlingvolgsysteem"
  ],
  [
    "Absences",
    "Afwezigheden"
  ],
  [
    "Registrations per month",
    "Aantal registraties per maand"
  ],
  [
    "Registrations per weekday",
    "Aantal registraties per weekdag"
  ],
  [
    "Registrations per code",
    "Aantal registraties per code"
  ],
  [
    "The charts count saved records with a known date.",
    "De grafieken tonen de bewaarde meldingen met een datum."
  ],
  [
    "Unknown school year",
    "Schooljaar onbekend"
  ],
  [
    "Type",
    "Type"
  ],
  [
    "Student note",
    "Leerlingennotitie"
  ],
  [
    "Notification",
    "Melding"
  ],
  [
    "Open the note to retrieve its full contents.",
    "Open de notitie om de volledige inhoud op te halen."
  ],
  [
    "Attachment: ",
    "Bijlage: "
  ],
  [
    "Document",
    "Document"
  ],
  [
    "Open attachment",
    "Bijlage openen"
  ],
  [
    "Record",
    "Dossier"
  ],
  [
    "Refresh note",
    "Notitie vernieuwen"
  ],
  [
    "Open note",
    "Notitie openen"
  ],
  [
    "Unknown date",
    "Datum onbekend"
  ],
  [
    "No matching records",
    "Geen overeenkomende registraties"
  ],
  [
    "New message",
    "Nieuw bericht"
  ],
  [
    "Forward message",
    "Bericht doorsturen"
  ],
  [
    "Reply to all",
    "Allen beantwoorden"
  ],
  [
    "Reply",
    "Beantwoorden"
  ],
  [
    "Resolve the original recipients: ",
    "Kies nog even wie dit bericht krijgt: "
  ],
  [
    "To",
    "Aan"
  ],
  [
    "Cc",
    "Kopie"
  ],
  [
    "Bcc",
    "Blinde kopie"
  ],
  [
    "To:",
    "Aan:"
  ],
  [
    "Cc:",
    "Kopie:"
  ],
  [
    "Bcc:",
    "Blinde kopie:"
  ],
  [
    " (Co-account)",
    " (Co-account)"
  ],
  [
    "Remove ",
    "Verwijder "
  ],
  [
    " co-account",
    " co-account"
  ],
  [
    " recipient ",
    " ontvanger "
  ],
  [
    "Name, class or school group",
    "Naam, klas of schoolgroep"
  ],
  [
    " recipient name or group",
    " naam of groep van ontvanger"
  ],
  [
    "Recipient",
    "Ontvanger"
  ],
  [
    "Add ",
    "Voeg "
  ],
  [
    " recipients",
    " ontvangers toe"
  ],
  [
    "Sending…",
    "Versturen…"
  ],
  [
    "Send",
    "Versturen"
  ],
  [
    "Send options",
    "Verzendopties"
  ],
  [
    "Save draft and close",
    "Concept opslaan en sluiten"
  ],
  [
    "This message will be sent to",
    "Dit bericht wordt verstuurd naar"
  ],
  [
    "Main accounts",
    "Hoofdaccounts"
  ],
  [
    "Co-accounts",
    "Co-accounts"
  ],
  [
    "Groups",
    "Groepen"
  ],
  [
    "Recipients",
    "Ontvangers"
  ],
  [
    "Main accounts, ",
    "Hoofdaccounts, "
  ],
  [
    " selected recipients",
    " geselecteerde ontvangers"
  ],
  [
    "Co-accounts, ",
    "Co-accounts, "
  ],
  [
    "Your school account does not allow messaging co-accounts.",
    "Je schoolaccount staat berichten naar co-accounts niet toe."
  ],
  [
    "Finding recipients…",
    "Ontvangers zoeken…"
  ],
  [
    "Choose a co-account linked to the school account.",
    "Kies een co-account dat aan het schoolaccount is gekoppeld."
  ],
  [
    "Search people, classes and school groups.",
    "Zoek personen, klassen en schoolgroepen."
  ],
  [
    "Searching…",
    "Zoeken…"
  ],
  [
    "Type at least two characters to find recipients.",
    "Typ minstens twee letters om iemand te zoeken."
  ],
  [
    "Suggestions will appear here.",
    "Suggesties verschijnen hier."
  ],
  [
    "Subject",
    "Onderwerp:"
  ],
  [
    "Message subject",
    "Onderwerp van bericht"
  ],
  [
    "Template",
    "Sjabloon"
  ],
  [
    "Greeting",
    "Begroeting"
  ],
  [
    "Attach files",
    "Bijlagen"
  ],
  [
    "Message text",
    "Berichttekst"
  ],
  [
    "Remove",
    "Verwijderen"
  ],
  [
    "Remove attachment ",
    "Verwijder bijlage "
  ],
  [
    "Edit",
    "Bewerken"
  ],
  [
    "Undo",
    "Ongedaan maken"
  ],
  [
    "Redo",
    "Opnieuw"
  ],
  [
    "Copy",
    "Kopiëren"
  ],
  [
    "Paste",
    "Plakken"
  ],
  [
    "Select all",
    "Alles selecteren"
  ],
  [
    "Formatting",
    "Opmaak"
  ],
  [
    "Bold",
    "Vet"
  ],
  [
    "Italic",
    "Cursief"
  ],
  [
    "Underline",
    "Onderstrepen"
  ],
  [
    "Clear formatting",
    "Opmaak wissen"
  ],
  [
    "Table",
    "Tabel"
  ],
  [
    "Insert table (2 × 2)",
    "Tabel invoegen (2 × 2)"
  ],
  [
    "Insert",
    "Invoegen"
  ],
  [
    "Link",
    "Link"
  ],
  [
    "Date",
    "Datum"
  ],
  [
    "View",
    "Bekijken"
  ],
  [
    "Increase text size",
    "Tekst vergroten"
  ],
  [
    "Decrease text size",
    "Tekst verkleinen"
  ],
  [
    "Font",
    "Lettertype"
  ],
  [
    "Text size",
    "Tekstgrootte"
  ],
  [
    "Blue text colour",
    "Tekstkleur blauw"
  ],
  [
    "Insert link",
    "Link invoegen"
  ],
  [
    "Remove link",
    "Link verwijderen"
  ],
  [
    "Insert smile",
    "Glimlach invoegen"
  ],
  [
    "Align left",
    "Links uitlijnen"
  ],
  [
    "Centre",
    "Centreren"
  ],
  [
    "Align right",
    "Rechts uitlijnen"
  ],
  [
    "Justify",
    "Uitvullen"
  ],
  [
    "Indent",
    "Inspringen"
  ],
  [
    "Outdent",
    "Uitspringen"
  ],
  [
    "Bulleted list",
    "Opsomming"
  ],
  [
    "Numbered list",
    "Genummerde lijst"
  ],
  [
    "Link address",
    "Linkadres"
  ],
  [
    "No subject",
    "Geen onderwerp"
  ],
  [
    "Loading message…",
    "Bericht laden…"
  ],
  [
    "Select a message",
    "Kies een bericht"
  ],
  [
    "Recipients: ",
    "Ontvangers: "
  ],
  [
    "Cc: ",
    "Kopie: "
  ],
  [
    "Bcc: ",
    "Blinde kopie: "
  ],
  [
    "Retry",
    "Opnieuw proberen"
  ],
  [
    "No message text.",
    "Geen berichttekst."
  ],
  [
    "Attachments",
    "Bijlagen"
  ],
  [
    "Attachment",
    "Bijlage"
  ],
  [
    "Offline · ",
    "Offline · "
  ],
  [
    "Message folder",
    "Berichtenmap"
  ],
  [
    " messages loaded",
    " berichten geladen"
  ],
  [
    "Refresh",
    "Vernieuwen"
  ],
  [
    "Loading…",
    "Laden…"
  ],
  [
    "Refresh this folder to confirm the previous message action before trying again.",
    "Vernieuw deze map even voor je het opnieuw probeert."
  ],
  [
    "Search subjects or senders",
    "Zoek op onderwerp of afzender"
  ],
  [
    "Search Smartschool messages",
    "Zoeken in Smartschool-berichten"
  ],
  [
    "Local drafts stay on this device.",
    "Lokale concepten blijven op dit apparaat."
  ],
  [
    "Messages",
    "Berichten"
  ],
  [
    "Search messages",
    "Zoeken in berichten"
  ],
  [
    "Subject or sender",
    "Onderwerp of afzender"
  ],
  [
    "Load older messages",
    "Oudere berichten laden"
  ],
  [
    "Unread. ",
    "Ongelezen. "
  ],
  [
    "Unknown sender",
    "Onbekende afzender"
  ],
  [
    "Attachments included",
    "Bevat bijlagen"
  ],
  [
    "Previous send accepted · check Sent",
    "Bericht verstuurd · kijk even bij Verzonden"
  ],
  [
    "Delivery unconfirmed · check Sent before retrying",
    "Niet zeker of het bericht verstuurd is · kijk eerst bij Verzonden"
  ],
  [
    "Discard draft",
    "Concept verwijderen"
  ],
  [
    "No matching messages",
    "Geen overeenkomende berichten"
  ],
  [
    "Your saved drafts will appear here.",
    "Je bewaarde concepten verschijnen hier."
  ],
  [
    "Press Refresh to load this folder.",
    "Klik op Vernieuwen om deze map te laden."
  ],
  [
    "Reply all",
    "Allen beantwoorden"
  ],
  [
    "Forward",
    "Doorsturen"
  ],
  [
    "Copy text",
    "Tekst kopiëren"
  ],
  [
    "Move to Trash",
    "Naar prullenmand"
  ],
  [
    "Create task / more actions",
    "Taak maken / meer acties"
  ],
  [
    "Message",
    "Bericht"
  ],
  [
    "Message unavailable",
    "Bericht niet beschikbaar"
  ],
  [
    "Retry message",
    "Bericht opnieuw laden"
  ],
  [
    "To: ",
    "Aan: "
  ],
  [
    "Message text copied",
    "Berichttekst gekopieerd"
  ],
  [
    "Download · ",
    "Downloaden · "
  ],
  [
    "Draft a reply with Gemini",
    "Antwoord opstellen met Gemini"
  ],
  [
    "Replies are unavailable for this message.",
    "Antwoorden zijn niet beschikbaar voor dit bericht."
  ],
  [
    "Generate an editable draft. Nothing is sent automatically.",
    "Maak een bewerkbaar concept. Er wordt niets automatisch verstuurd."
  ],
  [
    "Gemini API key required. Activate for details.",
    "Voeg eerst je Gemini API-sleutel toe. Klik voor meer uitleg."
  ],
  [
    "The message text is sent to Gemini when you request a draft. Review and edit the result before using it.",
    "Vraag je een antwoord aan Gemini? Dan delen we de berichttekst met Gemini. Lees het antwoord even na en pas het gerust aan."
  ],
  [
    "Create a local task",
    "Lokale taak maken"
  ],
  [
    "Keep this message as a task in your planner. Choose its due date.",
    "Bewaar dit bericht als taak in je planner. Kies een deadline."
  ],
  [
    "Due date for message task",
    "Deadline van berichttaak"
  ],
  [
    "Create task",
    "Taak maken"
  ],
  [
    "Task added to your planner",
    "Taak toegevoegd aan je planner"
  ],
  [
    "Inbox",
    "Postvak in"
  ],
  [
    "Sent",
    "Verzonden"
  ],
  [
    "Local drafts",
    "Lokale concepten"
  ],
  [
    "Trash",
    "Prullenmand"
  ],
  [
    "Scheduled",
    "Gepland"
  ],
  [
    "School drafts",
    "In ontwerp"
  ],
  [
    "No recipients selected",
    "Nog niemand gekozen"
  ],
  [
    "Offline file",
    "Offline bestand"
  ],
  [
    "Downloaded file",
    "Gedownload bestand"
  ],
  [
    "Saved on this computer. Removing this copy keeps the original school file.",
    "Bewaard op deze computer. Verwijder je deze kopie, dan blijft het bestand op school gewoon staan."
  ],
  [
    "Open",
    "Openen"
  ],
  [
    "Remove copy",
    "Kopie verwijderen"
  ],
  [
    "A password is needed to open this PDF.",
    "Een wachtwoord is nodig om deze PDF te openen."
  ],
  [
    "PDF password",
    "PDF-wachtwoord"
  ],
  [
    "Open PDF",
    "PDF openen"
  ],
  [
    "PDF page ",
    "PDF-pagina "
  ],
  [
    " of ",
    " van "
  ],
  [
    "This page has no selectable text.",
    "Je kunt op deze pagina geen tekst selecteren."
  ],
  [
    "PDF page text",
    "PDF-paginatekst"
  ],
  [
    "This PDF page could not be displayed. Download the file again, or try another page.",
    "Deze pagina lukt even niet. Download het bestand opnieuw of probeer een andere pagina."
  ],
  [
    "Loading PDF…",
    "PDF laden…"
  ],
  [
    "Previous",
    "Vorige"
  ],
  [
    "Page ",
    "Pagina "
  ],
  [
    "Next",
    "Volgende"
  ],
  [
    "Zoom out",
    "Uitzoomen"
  ],
  [
    "Fit page",
    "Pagina passend maken"
  ],
  [
    "Page width",
    "Paginabreedte"
  ],
  [
    "Zoom in",
    "Inzoomen"
  ],
  [
    "Page image",
    "Pagina-afbeelding"
  ],
  [
    "Page text",
    "Paginatekst"
  ],
  [
    "Filter by assignment type",
    "Filter op opdrachttype"
  ],
  [
    "All",
    "Alles"
  ],
  [
    "All courses",
    "Alle vakken"
  ],
  [
    "All types",
    "Alle soorten"
  ],
  [
    "Pinned only",
    "Vastgezet"
  ],
  [
    "Tasks grouped by due date",
    "Taken gegroepeerd op deadline"
  ],
  [
    "Week ahead",
    "Deze week"
  ],
  [
    " tasks",
    " taken"
  ],
  [
    "Busier days are taller · tests count extra",
    "Drukkere dagen zijn hoger · toetsen tellen extra"
  ],
  [
    "Working…",
    "Bezig…"
  ],
  [
    "Summarise with Gemini",
    "Samenvatten met Gemini"
  ],
  [
    "No unfinished tasks in the next seven days.",
    "Geen onafgewerkte taken in de komende zeven dagen."
  ],
  [
    "Missed · ",
    "Gemist · "
  ],
  [
    "Completed · ",
    "Klaar · "
  ],
  [
    "Restore ",
    "Herstel "
  ],
  [
    "Complete ",
    "Voltooi "
  ],
  [
    "  ·  posted ",
    "  ·  gepubliceerd "
  ],
  [
    "Unpin",
    "Losmaken"
  ],
  [
    "Pin",
    "Vastzetten"
  ],
  [
    "Pin updated",
    "Vastzetten bijgewerkt"
  ],
  [
    "All caught up · no missed tasks",
    "Helemaal bij · geen gemiste taken"
  ],
  [
    "No matching tasks",
    "Geen overeenkomende taken"
  ],
  [
    "Fetching the current presentation…",
    "Huidige presentatie ophalen…"
  ],
  [
    "Opening the presentation…",
    "Presentatie openen…"
  ],
  [
    "Current presentation · Smartschool / Microsoft PowerPoint",
    "Huidige presentatie · Smartschool / Microsoft PowerPoint"
  ],
  [
    "Teacher replacement presentation",
    "Presentatie leerkrachtvervangingen"
  ],
  [
    "Reports",
    "Rapporten"
  ],
  [
    "Available from Smartschool",
    "Beschikbaar via Smartschool"
  ],
  [
    "All school years",
    "Alle schooljaren"
  ],
  [
    "Filter report cards by school year",
    "Rapporten op schooljaar filteren"
  ],
  [
    "All periods",
    "Alle periodes"
  ],
  [
    "Period",
    "Periode"
  ],
  [
    "Choose school period",
    "Schoolperiode kiezen"
  ],
  [
    "Report cards",
    "Rapporten"
  ],
  [
    "Academic periods",
    "Schoolperiodes"
  ],
  [
    "Courses",
    "Vakken"
  ],
  [
    "School support",
    "Schoolondersteuning"
  ],
  [
    "School homepage",
    "Schoolstartpagina"
  ],
  [
    "School section",
    "Schoolonderdeel"
  ],
  [
    "School year",
    "Schooljaar"
  ],
  [
    "Grade period",
    "Periode"
  ],
  [
    "Choose academic period",
    "Schoolperiode kiezen"
  ],
  [
    "No offline files. Download a message attachment or report to keep a local copy.",
    "Nog geen offline bestanden. Download een bijlage of rapport om het hier te bewaren."
  ],
  [
    "No matching information. Press Refresh to check school access and availability.",
    "Niets gevonden. Klik op Vernieuwen om het nog eens te proberen."
  ],
  [
    "Report card",
    "Rapport"
  ],
  [
    "Saved report information · file unavailable",
    "Bewaarde rapportinformatie · bestand niet beschikbaar"
  ],
  [
    "View report",
    "Rapport bekijken"
  ],
  [
    "Download report",
    "Rapport downloaden"
  ],
  [
    "Download",
    "Downloaden"
  ],
  [
    "Synthetic workspace",
    "Voorbeeldwerkruimte"
  ],
  [
    "▾  Student support",
    "▾  Leerlingenbegeleiding"
  ],
  [
    "   ▾  School record",
    "   ▾  Schooldossier"
  ],
  [
    "Mark all as read",
    "Alles als gelezen markeren"
  ],
  [
    "Results",
    "Resultaten"
  ],
  [
    "Student notes",
    "Leerlingennotities"
  ],
  [
    "Filter results by school year",
    "Resultaten op schooljaar filteren"
  ],
  [
    "Averages",
    "Gemiddelden"
  ],
  [
    "All subjects",
    "Alle vakken"
  ],
  [
    "Filter results by subject",
    "Resultaten op vak filteren"
  ],
  [
    " periods ▾",
    " periodes ▾"
  ],
  [
    "All periods ▾",
    "Alle periodes ▾"
  ],
  [
    "Select all periods",
    "Alle periodes selecteren"
  ],
  [
    " · Does not count",
    " · Telt niet mee"
  ],
  [
    "Does not count",
    "Telt niet mee"
  ],
  [
    "No matching results",
    "Geen overeenkomende resultaten"
  ],
  [
    "Select a result",
    "Kies een resultaat"
  ],
  [
    "Details",
    "Details"
  ],
  [
    "Open details",
    "Details openen"
  ],
  [
    "Filter grades by subject",
    "Filter resultaten op vak"
  ],
  [
    "Notes",
    "Notities"
  ],
  [
    "This school year",
    "Dit schooljaar"
  ],
  [
    "This school year · Synthetic workspace",
    "Dit schooljaar · Voorbeeldwerkruimte"
  ],
  [
    "Period: ",
    "Periode: "
  ],
  [
    " · Clear",
    " · Wissen"
  ],
  [
    "Weighted counting results",
    "Gewogen meetellende resultaten"
  ],
  [
    " · due ",
    " · deadline "
  ],
  [
    "No matching items",
    "Geen overeenkomende items"
  ],
  [
    "Nothing available yet",
    "Nog niets beschikbaar"
  ],
  [
    "Close",
    "Sluiten"
  ],
  [
    "Waiting for account details",
    "Wachten op accountgegevens"
  ],
  [
    "Preparing your update",
    "Je update voorbereiden"
  ],
  [
    "Syncing your planner",
    "Je planner synchroniseren"
  ],
  [
    "Refreshing your workspace",
    "Je werkruimte vernieuwen"
  ],
  [
    "Complete the account window to continue.",
    "Vul het accountvenster in om verder te gaan."
  ],
  [
    "The planner will close when the update is ready.",
    "De planner sluit wanneer de update klaar is."
  ],
  [
    "Fetching your latest assignments, schedule, grades and LVS.",
    "Je nieuwste opdrachten, lessenrooster, resultaten en LVS ophalen."
  ],
  [
    "Updating the synthetic planner data.",
    "De voorbeeldgegevens van de planner bijwerken."
  ],
  [
    "Missed assignments",
    "Gemiste opdrachten"
  ],
  [
    "Completed assignments",
    "Afgewerkte taken"
  ],
  [
    " assignment",
    " opdracht"
  ],
  [
    " assignments",
    " opdrachten"
  ],
  [
    "Due ",
    "Deadline "
  ],
  [
    "My planner",
    "Mijn planner"
  ],
  [
    "Previous week",
    "Vorige week"
  ],
  [
    "Today",
    "Vandaag"
  ],
  [
    "Next week",
    "Volgende week"
  ],
  [
    "This week · ",
    "Deze week · "
  ],
  [
    "Search my planner…",
    "Zoeken in mijn planner…"
  ],
  [
    "Search my planner",
    "Zoeken in mijn planner"
  ],
  [
    "Show all",
    "Alles tonen"
  ],
  [
    "With assignments",
    "Met opdrachten"
  ],
  [
    "Lesson visibility",
    "Zichtbaarheid lessen"
  ],
  [
    "7 days",
    "7 dagen"
  ],
  [
    "5 days",
    "5 dagen"
  ],
  [
    "1 day",
    "1 dag"
  ],
  [
    "Number of days",
    "Aantal dagen"
  ],
  [
    "Week overview",
    "Weekoverzicht"
  ],
  [
    "Lesson list",
    "Lessenlijst"
  ],
  [
    ". Open lesson details",
    ". Lesdetails openen"
  ],
  [
    "Personal to-dos",
    "Eigen to-do’s"
  ],
  [
    "No assignments in this week. Lesson details and files remain available in the grid or lesson list.",
    "Geen taken deze week. Je lessen en bestanden staan nog gewoon in het rooster en de lessenlijst."
  ],
  [
    "Complete ",
    "Voltooien "
  ],
  [
    "Task completed",
    "Taak klaar"
  ],
  [
    "Task restored",
    "Taak weer open"
  ],
  [
    "Lessons without a time remain available in the lesson list.",
    "Lessen zonder uur blijven beschikbaar in de lessenlijst."
  ],
  [
    "Search",
    "Zoeken"
  ],
  [
    "Settings",
    "Instellingen"
  ],
  [
    "Sync now",
    "Nu synchroniseren"
  ],
  [
    "Teacher replacements",
    "Leerkrachtvervangingen"
  ],
  [
    "To-do",
    "Mijn taken"
  ],
  [
    "Overdue",
    "Gemist"
  ],
  [
    "Planner",
    "Planner"
  ],
  [
    "Grades",
    "Resultaten"
  ],
  [
    "Search tasks…",
    "Taken zoeken…"
  ],
  [
    "Search missed tasks…",
    "Gemiste taken zoeken…"
  ],
  [
    "Search schedule…",
    "Lessenrooster zoeken…"
  ],
  [
    "Search all classes…",
    "Alle lessen zoeken…"
  ],
  [
    "Search grades…",
    "Resultaten zoeken…"
  ],
  [
    "Search LVS…",
    "LVS zoeken…"
  ],
  [
    "Search current tab",
    "Huidig tabblad doorzoeken"
  ],
  [
    "Refresh synthetic data",
    "Voorbeeldgegevens vernieuwen"
  ],
  [
    "Sync warnings",
    "Even nakijken na het vernieuwen"
  ],
  [
    "Result details",
    "Resultaatdetails"
  ],
  [
    "Select an item",
    "Kies iets uit de lijst"
  ],
  [
    "Choose an item from the list to see its saved details.",
    "Kies een item uit de lijst om de bewaarde details te bekijken."
  ],
  [
    "Offline files",
    "Offline bestanden"
  ],
  [
    "AI required",
    "AI vereist"
  ],
  [
    "AI requires a Gemini API key. Add one in Settings → Change login details.",
    "AI vereist een Gemini API-sleutel. Voeg er een toe via Instellingen → Aanmeldgegevens wijzigen."
  ],
  [
    "Save downloaded file",
    "Gedownload bestand opslaan"
  ],
  [
    "Task details",
    "Taakdetails"
  ],
  [
    "Posted",
    "Gepubliceerd"
  ],
  [
    "Posted ",
    "Gepubliceerd "
  ],
  [
    "Save and close",
    "Bewaren en sluiten"
  ],
  [
    "⚑  Personal to-do · ",
    "⚑  Eigen to-do · "
  ],
  [
    "There is no content for this assignment.",
    "Er is geen inhoud bij deze opdracht."
  ],
  [
    "Instructions",
    "Instructies"
  ],
  [
    "Synthetic study material.",
    "Voorbeeldlesmateriaal."
  ],
  [
    "Files and links",
    "Bestanden en koppelingen"
  ],
  [
    "Offline",
    "Offline"
  ],
  [
    "Personal note",
    "Persoonlijke notitie"
  ],
  [
    "Task note",
    "Taaknotitie"
  ],
  [
    "Add a note…",
    "Voeg een notitie toe…"
  ],
  [
    " / 5,000 · only on this device",
    " / 5.000 · alleen op dit apparaat"
  ],
  [
    "Assignment details",
    "Opdrachtgegevens"
  ],
  [
    "Due",
    "Deadline"
  ],
  [
    "Course",
    "Vak"
  ],
  [
    "Teacher",
    "Leerkracht"
  ],
  [
    "Classroom",
    "Lokaal"
  ],
  [
    "Finish",
    "Afwerken"
  ],
  [
    "Complete assignment",
    "Opdracht voltooien"
  ],
  [
    "Assignment completed",
    "Opdracht voltooid"
  ],
  [
    "Open source message",
    "Bronbericht openen"
  ],
  [
    "Reload note",
    "Notitie vernieuwen"
  ],
  [
    "Loading note…",
    "Notitie laden…"
  ],
  [
    "Open link",
    "Link openen"
  ],
  [
    "What's new",
    "Wat is er nieuw"
  ],
  [
    "Update available",
    "Update beschikbaar"
  ],
  [
    "Update status",
    "Updatestatus"
  ],
  [
    "Install update",
    "Update installeren"
  ],
  [
    "Dismiss",
    "Sluiten"
  ],
  [
    "Could not complete the action",
    "De actie kon niet worden voltooid"
  ],
  [
    "Retry sync",
    "Synchronisatie opnieuw proberen"
  ],
  [
    "Change login details",
    "Inloggen aanpassen"
  ],
  [
    "LANGUAGE",
    "TAAL"
  ],
  [
    "Appearance",
    "Uiterlijk"
  ],
  [
    "RENDERING",
    "WEERGAVE"
  ],
  [
    "Full liquid lenses and an animated backdrop.",
    "Glazen knoppen met een rustig bewegende achtergrond."
  ],
  [
    "Compact workspace with opaque panels and a copper accent.",
    "Een rustige, compacte werkruimte met een koperkleurig accent."
  ],
  [
    "THEME",
    "THEMA"
  ],
  [
    "MODE",
    "KLEURMODUS"
  ],
  [
    "GLASS FROSTING",
    "MINDER DOORZICHTIG"
  ],
  [
    "Liquid glass frosting",
    "Matheid vloeibaar glas"
  ],
  [
    "From clear to frosted, independently of distortion.",
    "Van helder tot mat, onafhankelijk van vervorming."
  ],
  [
    "Clear",
    "Helder"
  ],
  [
    "Frosted",
    "Mat"
  ],
  [
    "DISTORTION",
    "VERVORMING"
  ],
  [
    "Liquid glass distortion",
    "Vervorming vloeibaar glas"
  ],
  [
    "Changes lens refraction independently of frosting.",
    "Past de lensbreking aan, onafhankelijk van matheid."
  ],
  [
    "None",
    "Geen"
  ],
  [
    "Strong",
    "Sterk"
  ],
  [
    "BACKGROUND",
    "ACHTERGROND"
  ],
  [
    "Silk",
    "Zijde"
  ],
  [
    "Soft colours",
    "Zachte kleuren"
  ],
  [
    "Aurora",
    "Aurora"
  ],
  [
    "Contour",
    "Contour"
  ],
  [
    "Background",
    "Achtergrond"
  ],
  [
    "TEXT SIZE",
    "TEKSTGROOTTE"
  ],
  [
    "Accessibility",
    "Toegankelijkheid"
  ],
  [
    "ACCESSIBILITY",
    "TOEGANKELIJKHEID"
  ],
  [
    "Reduced motion",
    "Minder beweging"
  ],
  [
    "Animated background",
    "Bewegende achtergrond"
  ],
  [
    "High contrast",
    "Hoog contrast"
  ],
  [
    "Account",
    "Account en bestanden"
  ],
  [
    "DATE CHECKER",
    "DATUMCONTROLE"
  ],
  [
    "AI date checking",
    "Datums nakijken met AI"
  ],
  [
    "Gemini checks assignment dates during sync. Verify dates marked with the sparkle icon.",
    "Gemini kijkt de datums na bij het vernieuwen. Kijk datums met een sterretje zelf nog even na."
  ],
  [
    "Local date checking. Turn on to use Gemini during sync.",
    "We kijken de datums op je computer na. Zet AI aan als je Gemini wilt gebruiken."
  ],
  [
    "Local date checking. Add a Gemini API key in login details to enable AI.",
    "We kijken de datums op je computer na. Voeg een Gemini API-sleutel toe bij je login om AI te gebruiken."
  ],
  [
    "ACCOUNT",
    "ACCOUNT"
  ],
  [
    "Copy sync diagnostics",
    "Info over vernieuwen kopiëren"
  ],
  [
    "Diagnostics copied",
    "Diagnose gekopieerd"
  ],
  [
    "Sync uses the selected date checker. Notes, pins and completed tasks are saved on this computer.",
    "Bij het vernieuwen gebruiken we jouw datumcontrole. Je notities, pins en afgewerkte taken blijven op deze computer bewaard."
  ],
  [
    "SYNTHETIC WORKSPACE",
    "VOORBEELDWERKRUIMTE"
  ],
  [
    "Light",
    "Licht"
  ],
  [
    "Dark",
    "Donker"
  ],
  [
    "System",
    "Systeem"
  ],
  [
    "English",
    "Engels"
  ],
  [
    "Dutch",
    "Nederlands"
  ],
  [
    "Drafts stay on this device for this account.",
    "Concepten blijven op dit apparaat voor dit account."
  ],
  [
    "⟳ Saved locally as a draft at ",
    "⟳ Lokaal opgeslagen als concept om "
  ],
  [
    "Draft is saved locally on this device.",
    "Concept wordt lokaal op dit apparaat bewaard."
  ],
  [
    "No missed assignments. Completed work stays in the completed collection.",
    "Geen gemiste opdrachten. Afgewerkt werk blijft bij de voltooide opdrachten."
  ],
  [
    "No completed assignments yet.",
    "Nog geen voltooide opdrachten."
  ],
  [
    "All caught up. No missed assignments.",
    "Helemaal bij. Geen gemiste opdrachten."
  ],
  [
    "Co-account",
    "Co-account"
  ],
  [
    "Unknown",
    "Onbekend"
  ],
  [
    "Auto",
    "Automatisch"
  ],
  [
    "Small",
    "Klein"
  ],
  [
    "Default",
    "Normaal"
  ],
  [
    "Large",
    "Groot"
  ],
  [
    "Vivid",
    "Levendig"
  ],
  [
    "Smartschool Planner · demo",
    "Smartschool Planner · demo"
  ],
  [
    "Last synced · 24 Oct, 09:00 · Synthetic workspace",
    "Laatst gesynchroniseerd · 24 okt, 09:00 · Voorbeeldwerkruimte"
  ],
  [
    "Open Smartschool",
    "Smartschool openen"
  ],
  [
    "Gemini reply saved in Local drafts",
    "Gemini-antwoord bewaard in Lokale concepten"
  ],
  [
    "View",
    "Beeld"
  ],
  [
    "Search co-accounts, such as parents.",
    "Zoek co-accounts, zoals ouders."
  ],
  [
    "Use Previous and Next to browse pages, and the zoom controls to enlarge them.",
    "Blader met Vorige en Volgende. Met de zoomknoppen maak je de pagina groter."
  ],
  [
    "Sends this week’s unfinished task instructions to Gemini. Dates stay unchanged. A Gemini API key is required.",
    "Deelt je open taken van deze week met Gemini voor een overzicht. Je datums veranderen niet. Hiervoor heb je een Gemini API-sleutel nodig."
  ],
  [
    "No additional instructions.",
    "Geen aanvullende instructies."
  ],
  [
    "Done",
    "Voltooid"
  ],
  [
    "The charts count saved records with a known date.",
    "De grafieken tellen opgeslagen registraties met een bekende datum."
  ],
  [
    "Resolve the original recipients: ",
    "Zoek de oorspronkelijke ontvangers: "
  ],
  [
    "Type at least two characters to find recipients.",
    "Typ minstens twee tekens om ontvangers te zoeken."
  ],
  [
    "Select a message",
    "Selecteer een bericht"
  ],
  [
    "Refresh this folder to confirm the previous message action before trying again.",
    "Vernieuw deze map om de vorige berichtactie te controleren voordat je het opnieuw probeert."
  ],
  [
    "Previous send accepted · check Sent",
    "Eerdere verzending geaccepteerd · controleer Verzonden"
  ],
  [
    "Delivery unconfirmed · check Sent before retrying",
    "Bezorging onbevestigd · controleer Verzonden voordat je opnieuw probeert"
  ],
  [
    "Gemini API key required. Activate for details.",
    "Gemini API-sleutel vereist. Activeer voor details."
  ],
  [
    "The message text is sent to Gemini when you request a draft. Review and edit the result before using it.",
    "De berichttekst wordt naar Gemini gestuurd wanneer je een concept vraagt. Controleer en bewerk het resultaat voordat je het gebruikt."
  ],
  [
    "No recipients selected",
    "Geen ontvangers geselecteerd"
  ],
  [
    "Saved on this computer. Removing this copy keeps the original school file.",
    "Bewaard op deze computer. Als je deze kopie verwijdert, blijft het originele schoolbestand behouden."
  ],
  [
    "This page has no selectable text.",
    "Deze pagina heeft geen selecteerbare tekst."
  ],
  [
    "This PDF page could not be displayed. Download the file again, or try another page.",
    "Deze PDF-pagina kon niet worden weergegeven. Download het bestand opnieuw of probeer een andere pagina."
  ],
  [
    "Completed · ",
    "Voltooid · "
  ],
  [
    "No offline files. Download a message attachment or report to keep a local copy.",
    "Geen offline bestanden. Download een berichtbijlage of rapport om een lokale kopie te bewaren."
  ],
  [
    "No matching information. Press Refresh to check school access and availability.",
    "Geen overeenkomende informatie. Klik op Vernieuwen om schooltoegang en beschikbaarheid te controleren."
  ],
  [
    "Select a result",
    "Selecteer een resultaat"
  ],
  [
    "Completed assignments",
    "Voltooide opdrachten"
  ],
  [
    "No assignments in this week. Lesson details and files remain available in the grid or lesson list.",
    "Geen opdrachten deze week. Lesdetails en bestanden blijven beschikbaar in het rooster of de lessenlijst."
  ],
  [
    "Task completed",
    "Taak voltooid"
  ],
  [
    "Task restored",
    "Taak hersteld"
  ],
  [
    "Sync warnings",
    "Synchronisatiewaarschuwingen"
  ],
  [
    "Select an item",
    "Selecteer een item"
  ],
  [
    "Change login details",
    "Aanmeldgegevens wijzigen"
  ],
  [
    "Appearance",
    "Weergave en leesbaarheid"
  ],
  [
    "Full liquid lenses and an animated backdrop.",
    "Volledige vloeibare lenzen en een bewegende achtergrond."
  ],
  [
    "Compact workspace with opaque panels and a copper accent.",
    "Compacte werkruimte met dekkende panelen en een koperkleurig accent."
  ],
  [
    "GLASS FROSTING",
    "GLASMATHEID"
  ],
  [
    "AI date checking",
    "Datums controleren met AI"
  ],
  [
    "Gemini checks assignment dates during sync. Verify dates marked with the sparkle icon.",
    "Gemini controleert datums tijdens synchronisatie. Controleer datums met het sterretje."
  ],
  [
    "Local date checking. Turn on to use Gemini during sync.",
    "Lokale datumcontrole. Schakel AI in om Gemini te gebruiken."
  ],
  [
    "Local date checking. Add a Gemini API key in login details to enable AI.",
    "Lokale datumcontrole. Voeg een Gemini API-sleutel toe bij de aanmeldgegevens."
  ],
  [
    "Copy sync diagnostics",
    "Diagnose synchronisatie kopiëren"
  ],
  [
    "Sync uses the selected date checker. Notes, pins and completed tasks are saved on this computer.",
    "Synchronisatie gebruikt de gekozen datumcontrole. Notities, vastgezette en voltooide taken worden op deze computer bewaard."
  ],
  [
    "Use Previous and Next to browse pages, and the zoom controls to enlarge them.",
    "Gebruik Vorige en Volgende om door pagina’s te bladeren en de zoomknoppen om ze te vergroten."
  ],
  [
    "Sends this week’s unfinished task instructions to Gemini. Dates stay unchanged. A Gemini API key is required.",
    "Stuurt de instructies van onafgewerkte taken van deze week naar Gemini. Datums blijven ongewijzigd. Een Gemini API-sleutel is vereist."
  ],
  [
    "All types",
    "Alle soorten"
  ],
  [
    "Silk",
    "Zijde"
  ],
  [
    "Soft colours",
    "Zachte kleuren"
  ],
  [
    "No matching tasks",
    "Geen taken gevonden"
  ],
  [
    "All caught up · no missed tasks",
    "Alles bij · geen gemiste taken"
  ],
  [
    "Tomorrow",
    "Morgen"
  ],
  [
    "This week",
    "Deze week"
  ],
  [
    "Pinned",
    "Vastgezet"
  ],
  [
    "Later",
    "Later"
  ],
  [
    "Completed",
    "Voltooid"
  ],
  [
    "Reduce motion",
    "Minder beweging"
  ],
  [
    "Animated background (Liquid Glass)",
    "Bewegende achtergrond (Liquid Glass)"
  ],
  [
    "Maximize",
    "Maximaliseren"
  ],
  [
    "Restore window",
    "Venster herstellen"
  ],
  [
    "Close window",
    "Venster sluiten"
  ],
  [
    "Published",
    "Gepubliceerd"
  ],
  [
    "My task",
    "Eigen taak"
  ],
  [
    "Empty",
    "Leeg"
  ],
  [
    "Typical · 36 tasks",
    "Voorbeeld · 36 taken"
  ],
  [
    "Stress · 1,000 tasks",
    "Belastingstest · 1.000 taken"
  ],
  [
    "Could not save settings. Check disk access and try again.",
    "De instellingen konden niet worden opgeslagen. Controleer de schijftoegang en probeer opnieuw."
  ],
  [
    "Could not save your rendering choice. Please try again.",
    "Je weergavekeuze kon niet worden opgeslagen. Probeer opnieuw."
  ],
  [
    "Could not change the date checker. Check your API key and login settings.",
    "De datumcontrole kon niet worden gewijzigd. Controleer je API-sleutel en aanmeldinstellingen."
  ],
  [
    "Could not save LVS read status. Please try again.",
    "De leesstatus van LVS kon niet worden opgeslagen. Probeer opnieuw."
  ],
  [
    "Sync this account before opening LVS notes.",
    "Synchroniseer dit account voordat je LVS-notities opent."
  ],
  [
    "Could not save your dismissal. Please try again.",
    "Je keuze kon niet worden opgeslagen. Probeer opnieuw."
  ],
  [
    "Local tasks could not be read. Existing files were kept.",
    "Lokale taken konden niet worden gelezen. Bestaande bestanden zijn bewaard."
  ],
  [
    "The school request expired or could not be saved. Please retry.",
    "De schoolaanvraag is verlopen of kon niet worden opgeslagen. Probeer opnieuw."
  ],
  [
    "The note is no longer available for this account. Sync LVS and try again.",
    "Deze notitie is niet meer beschikbaar voor dit account. Synchroniseer LVS en probeer opnieuw."
  ],
  [
    "Choose Liquid Glass or Smartschool in Settings before the first sync.",
    "Kies Liquid Glass of Smartschool in Instellingen voordat je voor het eerst synchroniseert."
  ],
  [
    "Sync this account before editing saved data.",
    "Synchroniseer dit account voordat je opgeslagen gegevens wijzigt."
  ],
  [
    "Could not save your change. The original data and your draft were kept. Check your login and disk access, then try again.",
    "Je wijziging kon niet worden opgeslagen. De oorspronkelijke gegevens en je concept zijn bewaard. Controleer je aanmelding en schijftoegang en probeer opnieuw."
  ],
  [
    "The file could not be downloaded. Retry the download to request a fresh link.",
    "Het bestand kon niet worden gedownload. Probeer opnieuw om een nieuwe downloadlink aan te vragen."
  ],
  [
    "The school or AI request could not be completed. Check your connection, account access and API key, then retry.",
    "De school- of AI-aanvraag kon niet worden voltooid. Controleer je verbinding, accounttoegang en API-sleutel en probeer opnieuw."
  ],
  [
    "AI requires a Gemini API key.",
    "Voor AI is een Gemini API-sleutel nodig."
  ],
  [
    "Wait for the current school request to finish.",
    "Wacht tot de huidige schoolaanvraag is afgerond."
  ],
  [
    "Account changed before the request.",
    "Het account is gewijzigd voordat de aanvraag begon."
  ],
  [
    "Sync this account first, or wait for the current request to finish.",
    "Synchroniseer dit account eerst of wacht tot de huidige aanvraag is afgerond."
  ],
  [
    "The move to Trash could not be confirmed. Refresh this folder before trying another message action.",
    "Het verplaatsen naar de prullenbak kon niet worden bevestigd. Vernieuw deze map voordat je een andere berichtactie uitvoert."
  ],
  [
    "This downloaded file has local changes. Save those changes elsewhere or remove the local copy before fetching the school version again.",
    "Dit gedownloade bestand heeft lokale wijzigingen. Bewaar die elders of verwijder de lokale kopie voordat je de schoolversie opnieuw ophaalt."
  ],
  [
    "The report could not be checked for changes. Your saved copy was kept; retry when connected.",
    "Het rapport kon niet op wijzigingen worden gecontroleerd. Je opgeslagen kopie is bewaard. Probeer opnieuw zodra je verbonden bent."
  ],
  [
    "The message action could not be saved safely. Check disk access before trying again.",
    "De berichtactie kon niet veilig worden opgeslagen. Controleer de schijftoegang voordat je opnieuw probeert."
  ],
  [
    "Use YYYY-MM-DD.",
    "Gebruik JJJJ-MM-DD."
  ],
  [
    "Open a message first.",
    "Open eerst een bericht."
  ],
  [
    "The local task could not be saved. Choose a valid YYYY-MM-DD date and sync this account.",
    "De lokale taak kon niet worden opgeslagen. Kies een geldige datum in JJJJ-MM-DD en synchroniseer dit account."
  ],
  [
    "This file cannot be opened. Download it again or check your account.",
    "Dit bestand kan niet worden geopend. Download het opnieuw of controleer je account."
  ],
  [
    "This file cannot be opened here. Use Save as to inspect it, or download it again.",
    "Dit bestand kan hier niet worden geopend. Gebruik Opslaan als om het te bekijken of download het opnieuw."
  ],
  [
    "File unavailable.",
    "Bestand niet beschikbaar."
  ],
  [
    "The file could not be saved. Your offline copy was kept.",
    "Het bestand kon niet worden opgeslagen. Je offline kopie is bewaard."
  ],
  [
    "Choose a local file.",
    "Kies een lokaal bestand."
  ],
  [
    "The offline copy could not be removed.",
    "De offline kopie kon niet worden verwijderd."
  ],
  [
    "Saved school information could not be read. Existing files were kept.",
    "Opgeslagen schoolgegevens konden niet worden gelezen. Bestaande bestanden zijn bewaard."
  ],
  [
    "The result could not be saved. Existing data was kept.",
    "Het resultaat kon niet worden opgeslagen. Bestaande gegevens zijn bewaard."
  ],
  [
    "The Gemini reply could not be saved. Your active draft was kept; check disk access and retry.",
    "Het Gemini-antwoord kon niet worden opgeslagen. Je huidige concept is bewaard. Controleer de schijftoegang en probeer opnieuw."
  ],
  [
    "This file type cannot be previewed or opened safely. Use Save as for the original file.",
    "Dit bestandstype kan niet veilig worden bekeken of geopend. Gebruik Opslaan als voor het oorspronkelijke bestand."
  ],
  [
    "This assignment is no longer available for editing. Sync again or open its lesson in Smartschool.",
    "Deze opdracht kan niet meer worden bewerkt. Synchroniseer opnieuw of open de bijbehorende les in Smartschool."
  ],
  [
    "The presentation could not load. Press Refresh to retry.",
    "De presentatie kon niet worden geladen. Kies Vernieuwen om opnieuw te proberen."
  ],
  [
    "Choose a date and time for your message.",
    "Kies een datum en tijd voor je bericht."
  ],
  [
    "Choose a valid date and time with a timezone.",
    "Kies een geldige datum en tijd met een tijdzone."
  ],
  [
    "That time has already passed. Choose a later time.",
    "Dat moment is al voorbij. Kies een later tijdstip."
  ],
  [
    "Scheduled sending is unavailable for this school account.",
    "Gepland versturen is niet beschikbaar voor dit schoolaccount."
  ],
  [
    "Choose a time within the next year.",
    "Kies een tijdstip binnen het komende jaar."
  ],
  [
    "Choose another time. This time is invalid or occurs twice when the clocks change.",
    "Kies een ander tijdstip. Dit tijdstip bestaat niet of komt twee keer voor bij de omschakeling van zomer- en wintertijd."
  ],
  [
    "AI requires a Gemini API key. Add one in login settings.",
    "Voor AI is een Gemini API-sleutel nodig. Voeg er een toe bij de aanmeldinstellingen."
  ],
  [
    "Gemini is unavailable or its usage limit has been reached. Try again later.",
    "Gemini is niet beschikbaar of de gebruikslimiet is bereikt. Probeer later opnieuw."
  ],
  [
    "Open a message before drafting a reply.",
    "Open een bericht voordat je een antwoord opstelt."
  ],
  [
    "This message has no text to reply to.",
    "Dit bericht bevat geen tekst om op te antwoorden."
  ],
  [
    "Gemini returned an invalid draft. Try again.",
    "Gemini gaf een ongeldig concept terug. Probeer opnieuw."
  ],
  [
    "Gemini returned an invalid weekly summary. Try again.",
    "Gemini gaf een ongeldig weekoverzicht terug. Probeer opnieuw."
  ],
  [
    "Gemini changed or omitted task information. Try again.",
    "Gemini heeft taakgegevens gewijzigd of weggelaten. Probeer opnieuw."
  ],
  [
    "Gemini could not complete this request. Check your API key and connection.",
    "Gemini kon deze aanvraag niet voltooien. Controleer je API-sleutel en verbinding."
  ],
  [
    "Gemini returned an empty or oversized answer. Try again.",
    "Gemini gaf een leeg of te groot antwoord terug. Probeer opnieuw."
  ],
  [
    "Gemini returned an unreadable answer. Try again.",
    "Gemini gaf een onleesbaar antwoord terug. Probeer opnieuw."
  ],
  [
    "This message is no longer in the selected folder. Refresh the folder first.",
    "Dit bericht staat niet meer in de geselecteerde map. Vernieuw de map eerst."
  ],
  [
    "The selected attachment changed. Select it again before sending.",
    "De geselecteerde bijlage is gewijzigd. Selecteer ze opnieuw voordat je verstuurt."
  ],
  [
    "The attachment upload could not be confirmed. No message was sent.",
    "Het uploaden van de bijlage kon niet worden bevestigd. Er is geen bericht verstuurd."
  ],
  [
    "This file does not belong to the selected message.",
    "Dit bestand hoort niet bij het geselecteerde bericht."
  ],
  [
    "The school returned a web page instead of a downloadable file.",
    "De school gaf een webpagina terug in plaats van een downloadbaar bestand."
  ],
  [
    "This file exceeds the 50 MB download limit.",
    "Dit bestand overschrijdt de downloadlimiet van 50 MB."
  ],
  [
    "This report is no longer available.",
    "Dit rapport is niet meer beschikbaar."
  ],
  [
    "The school returned an empty file.",
    "De school gaf een leeg bestand terug."
  ],
  [
    "The school did not return a PDF report.",
    "De school gaf geen pdf-rapport terug."
  ],
  [
    "LVS note",
    "LVS-notitie"
  ],
  [
    "Counts toward total",
    "Telt mee voor het totaal"
  ],
  [
    "Result",
    "Resultaat"
  ],
  [
    "School address not found",
    "Schooladres niet gevonden"
  ],
  [
    "School address looks wrong",
    "Het schooladres lijkt niet te kloppen"
  ],
  [
    "Secure connection failed",
    "Beveiligde verbinding mislukt"
  ],
  [
    "Can't reach Smartschool",
    "Smartschool is niet bereikbaar"
  ],
  [
    "Smartschool has a problem",
    "Er is een probleem bij Smartschool"
  ],
  [
    "Smartschool refused the login",
    "Smartschool heeft de aanmelding geweigerd"
  ],
  [
    "Unexpected answer from Smartschool",
    "Onverwacht antwoord van Smartschool"
  ],
  [
    "2FA component missing",
    "Onderdeel voor tweestapsverificatie ontbreekt"
  ],
  [
    "Login failed",
    "Aanmelden mislukt"
  ],
  [
    "Login details incomplete",
    "Aanmeldgegevens onvolledig"
  ],
  [
    "Could not verify the signed-in account",
    "Het aangemelde account kon niet worden gecontroleerd"
  ],
  [
    "Login details unreadable",
    "Aanmeldgegevens onleesbaar"
  ],
  [
    "Something went wrong",
    "Er is iets misgegaan"
  ],
  [
    "The school address in your login details isn't valid.",
    "Het schooladres in je aanmeldgegevens is ongeldig."
  ],
  [
    "Fix it under Change login details (for example yourschool.smartschool.be).",
    "Pas het aan bij Aanmeldgegevens wijzigen, bijvoorbeeld jouwschool.smartschool.be."
  ],
  [
    "This is on their side. Wait a few minutes and press Retry.",
    "Het probleem ligt bij Smartschool. Wacht enkele minuten en kies Opnieuw proberen."
  ],
  [
    "Smartschool didn't let this account in.",
    "Smartschool heeft dit account niet toegelaten."
  ],
  [
    "Smartschool didn't accept the login.",
    "Smartschool heeft de aanmelding niet aanvaard."
  ],
  [
    "Smartschool kept sending back the login page, so the login wasn't accepted.",
    "Smartschool bleef de aanmeldpagina terugsturen. De aanmelding is niet aanvaard."
  ],
  [
    "Your account uses an authenticator app, but the 2FA component isn't available.",
    "Je account gebruikt een authenticator-app, maar het onderdeel voor tweestapsverificatie is niet beschikbaar."
  ],
  [
    "Reinstall the latest version of the app.",
    "Installeer de nieuwste versie van de app opnieuw."
  ],
  [
    "Open Change login details and fill them in.",
    "Open Aanmeldgegevens wijzigen en vul de ontbrekende gegevens in."
  ],
  [
    "Smartschool did not return account information the planner could read.",
    "Smartschool gaf geen accountgegevens terug die de planner kon lezen."
  ],
  [
    "Check your saved login details. If they are correct, the Smartschool login response may have changed.",
    "Controleer je opgeslagen aanmeldgegevens. Als die kloppen, is het antwoord van Smartschool mogelijk gewijzigd."
  ],
  [
    "The saved login details file is missing or damaged.",
    "Het bestand met opgeslagen aanmeldgegevens ontbreekt of is beschadigd."
  ],
  [
    "Open Change login details and enter them again.",
    "Open Aanmeldgegevens wijzigen en voer ze opnieuw in."
  ],
  [
    "The operation could not be completed. Open Technical details to see where it failed.",
    "De actie kon niet worden voltooid. Open Technische details om te zien waar het misging."
  ],
  [
    "Press Retry. If it keeps happening, open Technical details below and report it.",
    "Kies Opnieuw proberen. Als het probleem blijft bestaan, open dan Technische details hieronder en meld het."
  ],
  [
    "Check the school address under Change login details. It should look like yourschool.smartschool.be, without https:// or slashes.",
    "Controleer het schooladres bij Aanmeldgegevens wijzigen. Gebruik bijvoorbeeld jouwschool.smartschool.be, zonder https:// of schuine strepen."
  ],
  [
    "Check your details, then press Retry. Don't keep retrying with a wrong password - Smartschool can temporarily lock the account.",
    "Controleer je gegevens en kies Opnieuw proberen. Blijf niet proberen met een onjuist wachtwoord: Smartschool kan het account tijdelijk blokkeren."
  ],
  [
    "Check that your computer's date and time are correct, and that no VPN, proxy or security program is interfering. Then press Retry.",
    "Controleer de datum en tijd op je computer en kijk of een VPN, proxy of beveiligingsprogramma de verbinding blokkeert. Kies daarna Opnieuw proberen."
  ],
  [
    "Check your internet connection and that the school address in your login details is right (for example yourschool.smartschool.be). Then press Retry.",
    "Controleer je internetverbinding en het schooladres in je aanmeldgegevens, bijvoorbeeld jouwschool.smartschool.be. Kies daarna Opnieuw proberen."
  ],
  [
    "Gemini key not working",
    "Gemini-sleutel werkt niet"
  ],
  [
    "Gemini limit reached",
    "Gemini-limiet bereikt"
  ],
  [
    "Gemini unavailable",
    "Gemini niet beschikbaar"
  ],
  [
    "Gemini answered unclearly",
    "Gemini gaf een onduidelijk antwoord"
  ],
  [
    "Gemini couldn't be used",
    "Gemini kon niet worden gebruikt"
  ],
  [
    "Saved drafts could not be read. Existing files were kept.",
    "Opgeslagen concepten konden niet worden gelezen. Bestaande bestanden zijn bewaard."
  ],
  [
    "Your latest draft was recovered in memory. Keep this window open until it can be saved.",
    "Je laatste concept is in het geheugen hersteld. Houd dit venster open tot het kan worden opgeslagen."
  ],
  [
    "A draft from another account could not be saved. It is kept privately in memory; switch back to recover it.",
    "Een concept van een ander account kon niet worden opgeslagen. Het blijft afgeschermd in het geheugen bewaard. Schakel terug om het te herstellen."
  ],
  [
    "This draft exceeds the subject (250) or message (100,000) character limit. Shorten it before closing; your text is still here.",
    "Dit concept overschrijdt de tekenlimiet voor het onderwerp (250) of bericht (100.000). Kort het in voordat je sluit. Je tekst staat hier nog."
  ],
  [
    "This draft could not be removed. Existing files were kept.",
    "Dit concept kon niet worden verwijderd. Bestaande bestanden zijn bewaard."
  ],
  [
    "A draft from another account is not saved yet. Switch back to recover it before closing the app.",
    "Een concept van een ander account is nog niet opgeslagen. Schakel terug om het te herstellen voordat je de app sluit."
  ],
  [
    "Formatted message is too large. Shorten it before closing.",
    "Het opgemaakte bericht is te groot. Kort het in voordat je sluit."
  ],
  [
    "Formatted message is too large.",
    "Het opgemaakte bericht is te groot."
  ],
  [
    "Choose up to 20 local files, at most 50 MB together. Unreadable files were not attached.",
    "Kies maximaal 20 lokale bestanden, samen hoogstens 50 MB. Onleesbare bestanden zijn niet toegevoegd."
  ],
  [
    "This school message does not allow replies.",
    "Op dit schoolbericht kan niet worden geantwoord."
  ],
  [
    "The generated reply could not be saved. Your current draft was kept.",
    "Het gegenereerde antwoord kon niet worden opgeslagen. Je huidige concept is bewaard."
  ],
  [
    "Wait for the current school request or sync this account, then retry.",
    "Wacht tot de huidige schoolaanvraag is afgerond of synchroniseer dit account. Probeer daarna opnieuw."
  ],
  [
    "Waiting for the current school request before finding people…",
    "We wachten tot de huidige schoolaanvraag is afgerond voordat we personen zoeken…"
  ],
  [
    "Enter between 2 and 100 characters to find a recipient.",
    "Voer 2 tot 100 tekens in om een ontvanger te zoeken."
  ],
  [
    "A message can have up to 100 selected recipients.",
    "Een bericht kan maximaal 100 geselecteerde ontvangers hebben."
  ],
  [
    "Wait for the current school request to finish, then retry.",
    "Wacht tot de huidige schoolaanvraag is afgerond en probeer opnieuw."
  ],
  [
    "Choose a recipient, enter a subject (up to 250 characters) and a message (up to 100,000 characters).",
    "Kies een ontvanger en voer een onderwerp (maximaal 250 tekens) en bericht (maximaal 100.000 tekens) in."
  ],
  [
    "Delivery could not be confirmed. Check Sent in Smartschool before starting another message. Your draft was kept.",
    "De verzending kon niet worden bevestigd. Controleer Verzonden in Smartschool voordat je een nieuw bericht opstelt. Je concept is bewaard."
  ],
  [
    "Delivery could not be confirmed. Check Sent in Smartschool before starting another message.",
    "De verzending kon niet worden bevestigd. Controleer Verzonden in Smartschool voordat je een nieuw bericht opstelt."
  ],
  [
    "Message was not sent. Check your connection and selected recipient, then retry. Your draft was kept.",
    "Het bericht is niet verstuurd. Controleer je verbinding en de geselecteerde ontvanger en probeer opnieuw. Je concept is bewaard."
  ],
  [
    "Files could not be attached. Choose readable local files, at most 20 files and 50 MB together.",
    "De bestanden konden niet worden toegevoegd. Kies leesbare lokale bestanden, maximaal 20 bestanden en samen hoogstens 50 MB."
  ],
  [
    "Suggestions could not be loaded. Check your connection, then keep typing or press Enter to retry.",
    "Suggesties konden niet worden geladen. Controleer je verbinding. Typ daarna verder of druk op Enter om opnieuw te proberen."
  ],
  [
    "Your school account does not allow messaging co-accounts. Choose a main account instead.",
    "Je schoolaccount kan geen berichten naar co-accounts sturen. Kies een hoofdaccount."
  ],
  [
    "No matching people or groups found. Try another name.",
    "Geen passende personen of groepen gevonden. Probeer een andere naam."
  ],
  [
    "Send request accepted. Check Scheduled in Smartschool before scheduling this again.",
    "De verzendaanvraag is aanvaard. Controleer Gepland in Smartschool voordat je dit opnieuw plant."
  ],
  [
    "Send request accepted. Check Sent in Smartschool before sending this again.",
    "De verzendaanvraag is aanvaard. Controleer Verzonden in Smartschool voordat je dit opnieuw verstuurt."
  ],
  [
    "This request expired. Your draft was kept; retry when ready.",
    "Deze aanvraag is verlopen. Je concept is bewaard. Probeer opnieuw wanneer je klaar bent."
  ],
  [
    "The message was not scheduled. Check your school scheduling permissions, chosen time and connection. Your draft was kept.",
    "Het bericht is niet ingepland. Controleer je schoolrechten voor gepland versturen, het gekozen tijdstip en je verbinding. Je concept is bewaard."
  ],
  [
    "Delivery could not be confirmed. Check Scheduled and Sent in Smartschool before starting another message. Your draft was kept.",
    "De verzending kon niet worden bevestigd. Controleer Gepland en Verzonden in Smartschool voordat je een nieuw bericht opstelt. Je concept is bewaard."
  ],
  [
    "Delivery could not be confirmed. Check Scheduled and Sent in Smartschool before starting another message.",
    "De verzending kon niet worden bevestigd. Controleer Gepland en Verzonden in Smartschool voordat je een nieuw bericht opstelt."
  ],
  [
    "Send request accepted. Check Scheduled and Sent in Smartschool before sending this again.",
    "De verzendaanvraag is aanvaard. Controleer Gepland en Verzonden in Smartschool voordat je dit opnieuw verstuurt."
  ],
  [
    "This draft could not be saved. Keep this window open and retry.",
    "Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Choose the school recipients explicitly before sending. ",
    "Kies de ontvangers van de school voordat je verstuurt. "
  ],
  [
    "Choose who should receive this forwarded message. ",
    "Kies wie dit doorgestuurde bericht moet ontvangen. "
  ],
  [
    "Original attachments are not automatically forwarded; attach any local copies you want to include.",
    "Oorspronkelijke bijlagen worden niet automatisch doorgestuurd. Voeg de lokale kopieën toe die je wilt meesturen."
  ],
  [
    "This draft has a previous send attempt. Check Sent in Smartschool before starting another message.",
    "Er is al een verzendpoging voor dit concept. Controleer Verzonden in Smartschool voordat je een nieuw bericht opstelt."
  ],
  [
    "This draft has a previous send attempt. Check Scheduled and Sent in Smartschool before starting another message.",
    "Er is al een verzendpoging voor dit concept. Controleer Gepland en Verzonden in Smartschool voordat je een nieuw bericht opstelt."
  ],
  [
    "The previous update could not finish. Your existing app was kept. Try the update again.",
    "De vorige update kon niet worden afgerond. Je bestaande app is bewaard. Probeer de update opnieuw."
  ],
  [
    "Choose the school recipients explicitly before sending. Original attachments are not automatically forwarded; attach any local copies you want to include.",
    "Kies de ontvangers van de school voordat je verstuurt. Oorspronkelijke bijlagen worden niet automatisch doorgestuurd. Voeg de lokale kopieën toe die je wilt meesturen."
  ],
  [
    "Choose who should receive this forwarded message. Original attachments are not automatically forwarded; attach any local copies you want to include.",
    "Kies wie dit doorgestuurde bericht moet ontvangen. Oorspronkelijke bijlagen worden niet automatisch doorgestuurd. Voeg de lokale kopieën toe die je wilt meesturen."
  ],
  [
    "Delivery could not be confirmed. Check Sent in Smartschool before starting another message. Your draft was kept. This draft could not be saved. Keep this window open and retry.",
    "De verzending kon niet worden bevestigd. Controleer Verzonden in Smartschool voordat je een nieuw bericht opstelt. Je concept is bewaard. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Delivery could not be confirmed. Check Sent in Smartschool before starting another message. This draft could not be saved. Keep this window open and retry.",
    "De verzending kon niet worden bevestigd. Controleer Verzonden in Smartschool voordat je een nieuw bericht opstelt. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Send request accepted. Check Scheduled in Smartschool before scheduling this again. This draft could not be saved. Keep this window open and retry.",
    "De verzendaanvraag is aanvaard. Controleer Gepland in Smartschool voordat je dit opnieuw plant. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Send request accepted. Check Sent in Smartschool before sending this again. This draft could not be saved. Keep this window open and retry.",
    "De verzendaanvraag is aanvaard. Controleer Verzonden in Smartschool voordat je dit opnieuw verstuurt. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Delivery could not be confirmed. Check Scheduled and Sent in Smartschool before starting another message. Your draft was kept. This draft could not be saved. Keep this window open and retry.",
    "De verzending kon niet worden bevestigd. Controleer Gepland en Verzonden in Smartschool voordat je een nieuw bericht opstelt. Je concept is bewaard. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Delivery could not be confirmed. Check Scheduled and Sent in Smartschool before starting another message. This draft could not be saved. Keep this window open and retry.",
    "De verzending kon niet worden bevestigd. Controleer Gepland en Verzonden in Smartschool voordat je een nieuw bericht opstelt. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ],
  [
    "Send request accepted. Check Scheduled and Sent in Smartschool before sending this again. This draft could not be saved. Keep this window open and retry.",
    "De verzendaanvraag is aanvaard. Controleer Gepland en Verzonden in Smartschool voordat je dit opnieuw verstuurt. Dit concept kon niet worden opgeslagen. Houd dit venster open en probeer opnieuw."
  ]
];

var english = {};
var dutch = {};
var canonicalDutch = {};
for (var i = 0; i < pairs.length; ++i) {
    if (!(pairs[i][0] in canonicalDutch)) canonicalDutch[pairs[i][0]] = pairs[i][1];
    if (!(pairs[i][0] in english)) english[pairs[i][0]] = pairs[i][0];
    if (!(pairs[i][1] in english)) english[pairs[i][1]] = pairs[i][0];
}
for (var key in english) dutch[key] = canonicalDutch[english[key]];
// Only complete app-authored templates are formatted; captured values remain unchanged.
var formattedPairs = [
    ["Couldn't make a secure connection to Smartschool%1.", "Er kon geen beveiligde verbinding met Smartschool%1 worden gemaakt."],
    ["Couldn't connect to Smartschool%1.", "Er kon geen verbinding met Smartschool%1 worden gemaakt."],
    ["Smartschool%1 kept redirecting without ever loading a page.", "Smartschool%1 bleef doorverwijzen zonder een pagina te laden."],
    ["Smartschool answered with an error (HTTP %1).", "Smartschool gaf een fout terug (HTTP %1)."],
    ["Smartschool answered with HTTP %1%2.", "Smartschool antwoordde met HTTP %1%2."],
    ["Smartschool answered \"page not found\" (HTTP 404)%1. That usually means the school address is wrong.", "Smartschool antwoordde met \"pagina niet gevonden\" (HTTP 404)%1. Meestal klopt het schooladres dan niet."],
    ["The school address \"%1\" isn't in the right format.", "Het schooladres \"%1\" heeft niet de juiste vorm."],
    ["Some required login details are empty: %1.", "Enkele verplichte aanmeldgegevens ontbreken: %1."],
    ["Version %1 is available.", "Versie %1 is beschikbaar."]
];
function lookup(text, language) {
    var labels = language === "nl" ? dutch : english;
    if (Object.prototype.hasOwnProperty.call(labels, text)) return labels[text];
    for (var i = 0; i < formattedPairs.length; ++i) {
        for (var from = 0; from < 2; ++from) {
            var expression = formattedPairs[i][from].replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%[12]/g, "(.*?)");
            var match = new RegExp("^" + expression + "$").exec(text);
            if (match) return formattedPairs[i][language === "nl" ? 1 : 0].replace(/%([12])/g, function(_, index) { return match[Number(index)]; });
        }
    }
    return undefined;
}
function translate(text, language) {
    var value = lookup(text, language);
    if (value !== undefined) return value;
    // Translate combined app labels only when every part is known.
    var separator = text.indexOf("\n") >= 0 ? "\n" : " · ";
    var parts = text.split(separator);
    var translated = parts.map(function(part) { return part === "" ? "" : lookup(part, language); });
    if (parts.length > 1 && translated.every(function(part) { return part !== undefined; })) return translated.join(separator);
    return text;
}
function t(text, language) { return translate(text, language); }
