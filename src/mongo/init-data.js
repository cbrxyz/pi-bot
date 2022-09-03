db = db.getSiblingDB('data');

// Set up censor data
db.censor.insertOne(
  {
    words: [
      'pineapple',
      'kangaroo',
      'cow'
    ],
    emojis: [
      '\U0001F595' // Middle finger emoji
    ]
  }
);

// Set up event data
db.events.insertMany([
  {
    name: "Anatomy and Physiology",
    aliases: [
      "anat",
      "anatomy",
      "ap"
    ]
  },
  {
    name: "Astronomy",
    aliases: [
      "astro"
    ]
  },
  {
    name: "Robot Tour",
    aliases: []
  }
]);

// Set up invitational data
db.invitationals.insertMany([
  {
    official_name: "Bernard Invitational",
    channel_name: "bernard",
    emoji: "🐶",
    aliases: [
      "doggo"
    ],
    tourney_date: { "$date": "2023-12-10T00:00:00.000Z" },
    open_days: 10,
    closed_days: 30,
    voters: [],
    status: "archived"
  },
  {
    official_name: "Big Bear Invitational",
    channel_name: "bigbear",
    emoji: "🐻",
    aliases: [
      "bearasauras"
    ],
    tourney_date: { "$date": "2024-02-12T00:00:00.000Z" },
    open_days: 10,
    closed_days: 30,
    voters: [],
    status: "open"
  }
]);

// Set up settings
db.settings.insertOne({
  custom_bot_status_text: null,
  custom_bot_status_type: null,
  invitational_season: 2023
});
