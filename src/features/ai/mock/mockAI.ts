import type {
  AIChatResponse,
  BudgetAdviceRequest,
  BudgetAdviceResponse,
  ChatHistoryResponse,
  LocalityRecommendationRequest,
  LocalityRecommendationResponse,
  PersonalizedSuggestionsResponse,
  ScamCheckRequest,
  ScamCheckResponse,
} from "@/features/ai/types";

const delay = (milliseconds: number) =>
  new Promise((resolve) =>
    setTimeout(resolve, milliseconds)
  );

const chatHistory: ChatHistoryResponse["items"] = [
  {
    id: "assistant-welcome",
    role: "assistant",
    content:
      "Hi! I’m your ShaharSaathi AI relocation assistant. I can help you compare localities, plan your monthly budget, understand transport options, and identify suspicious rental listings.",
    created_at: new Date().toISOString(),
  },
];

export async function mockSendChatMessage(
  question: string
): Promise<AIChatResponse> {
  await delay(900);

  const normalizedQuestion =
    question.toLowerCase();

  let answer =
    "I can help you with housing, locality selection, budgeting, transport, safety, and relocation planning. Share your city, monthly budget, occupation, and preferred commute so I can give you more personalized guidance.";

  if (
    normalizedQuestion.includes("delhi") &&
    normalizedQuestion.includes("student")
  ) {
    answer =
      "For a student relocating to Delhi, consider areas such as Laxmi Nagar, Mukherjee Nagar, Satya Niketan, and Rohini depending on your college location and budget. Prioritize metro connectivity, verified listings, nearby food options, and a commute under 45 minutes.";
  } else if (
    normalizedQuestion.includes("budget") ||
    normalizedQuestion.includes("expense")
  ) {
    answer =
      "A practical relocation budget should separate rent, deposit, food, transport, utilities, and emergency savings. Try to keep rent near 30–40% of your monthly income and retain at least one month of essential expenses as an emergency reserve.";
  } else if (
    normalizedQuestion.includes("scam") ||
    normalizedQuestion.includes("fraud")
  ) {
    answer =
      "Avoid listings that demand advance payment before a visit, refuse video calls, offer unrealistically low rent, create artificial urgency, or cannot provide ownership documents. Always verify the property and owner before transferring money.";
  } else if (
    normalizedQuestion.includes("metro") ||
    normalizedQuestion.includes("transport")
  ) {
    answer =
      "Choose a locality with reliable last-mile connectivity and a nearby metro or bus route. Compare total commute time, interchange count, peak-hour crowding, and monthly travel cost instead of considering distance alone.";
  }

  const message = {
    id: `assistant-${Date.now()}`,
    role: "assistant" as const,
    content: answer,
    created_at: new Date().toISOString(),
  };

  chatHistory.push({
    id: `user-${Date.now()}`,
    role: "user",
    content: question,
    created_at: new Date().toISOString(),
  });

  chatHistory.push(message);

  return {
    answer,
    message,
  };
}

export async function mockGetChatHistory(): Promise<ChatHistoryResponse> {
  await delay(400);

  return {
    items: [...chatHistory],
  };
}

export async function mockClearChatHistory(): Promise<{
  success: boolean;
  message: string;
}> {
  await delay(350);

  chatHistory.splice(
    0,
    chatHistory.length
  );

  chatHistory.push({
    id: "assistant-welcome",
    role: "assistant",
    content:
      "Chat history cleared. Tell me where you are planning to relocate and I’ll help you get started.",
    created_at: new Date().toISOString(),
  });

  return {
    success: true,
    message:
      "Chat history cleared successfully.",
  };
}

export async function mockGetLocalityRecommendations(
  payload: LocalityRecommendationRequest
): Promise<LocalityRecommendationResponse> {
  await delay(1200);

  const city =
    payload.city.trim() || "Delhi";

  return {
    recommendations: [
      {
        id: "locality-1",
        locality: "Laxmi Nagar",
        city,
        average_rent: Math.min(
          payload.budget,
          12000
        ),
        safety_score: 78,
        nearby_metro:
          "Laxmi Nagar Metro Station",
        commute_summary:
          "Strong metro access with convenient connectivity to central and east Delhi.",
        nearby_essentials: [
          "Grocery stores",
          "Affordable food outlets",
          "Pharmacies",
          "Coaching centres",
        ],
        pros: [
          "Affordable for students and early professionals",
          "Good metro connectivity",
          "Many shared accommodation options",
        ],
        cons: [
          "Crowded during peak hours",
          "Parking availability can be limited",
        ],
      },
      {
        id: "locality-2",
        locality: "Rohini",
        city,
        average_rent: Math.min(
          payload.budget,
          14500
        ),
        safety_score: 84,
        nearby_metro:
          "Rohini West Metro Station",
        commute_summary:
          "Well-connected residential area with planned sectors and multiple metro stations.",
        nearby_essentials: [
          "Hospitals",
          "Shopping centres",
          "Parks",
          "Local markets",
        ],
        pros: [
          "Planned residential neighbourhoods",
          "Good access to daily essentials",
          "Suitable for long-term stays",
        ],
        cons: [
          "Longer commute to some central locations",
          "Rent varies significantly by sector",
        ],
      },
      {
        id: "locality-3",
        locality: "Dwarka",
        city,
        average_rent: Math.min(
          payload.budget,
          16000
        ),
        safety_score: 87,
        nearby_metro:
          "Dwarka Sector 12 Metro Station",
        commute_summary:
          "Reliable metro corridor with access to the airport and western Delhi.",
        nearby_essentials: [
          "Supermarkets",
          "Hospitals",
          "Schools",
          "Community markets",
        ],
        pros: [
          "Clean and organised surroundings",
          "Strong metro connectivity",
          "Good residential infrastructure",
        ],
        cons: [
          "Some sectors may exceed a student budget",
          "Last-mile travel may be needed in a few areas",
        ],
      },
    ],
  };
}

export async function mockCheckScam(
  payload: ScamCheckRequest
): Promise<ScamCheckResponse> {
  await delay(1100);

  const normalizedContent =
    payload.content.toLowerCase();

  const suspiciousSignals = [
    "advance",
    "urgent",
    "immediately",
    "token money",
    "no visit",
    "without visit",
    "owner abroad",
    "pay first",
    "limited time",
  ];

  const detectedSignals =
    suspiciousSignals.filter((signal) =>
      normalizedContent.includes(signal)
    );

  const score = Math.min(
    35 + detectedSignals.length * 12,
    96
  );

  const risk =
    score >= 70
      ? ("High" as const)
      : score >= 40
        ? ("Medium" as const)
        : ("Low" as const);

  const reasons =
    detectedSignals.length > 0
      ? detectedSignals.map(
          (signal) =>
            `The listing contains the suspicious phrase or behaviour: "${signal}".`
        )
      : [
          "No major high-risk scam phrase was detected.",
          "The listing should still be verified before making payment.",
        ];

  return {
    risk_level: risk,
    risk_score: score,
    summary:
      "Mock rental scam assessment generated for testing.",
    red_flags: reasons,
    positive_signals: [],
    recommendations: [
      "Visit the property before making any payment.",
      "Verify the owner's identity and ownership documents.",
      "Avoid advance payments before verification.",
    ],
    disclaimer:
      "This is an AI-based risk assessment and not a legal guarantee.",
  };
}

export async function mockGetBudgetAdvice(
  payload: BudgetAdviceRequest
): Promise<BudgetAdviceResponse> {
  await delay(1000);

  const totalExpenses =
    payload.rent +
    payload.food +
    payload.transport +
    payload.utilities +
    payload.other_expenses;

  const remainingAmount =
    payload.monthly_income -
    totalExpenses;

  const savingsRate =
    payload.monthly_income > 0
      ? Number(
          (
            (payload.savings /
              payload.monthly_income) *
            100
          ).toFixed(1)
        )
      : 0;

  const rentPercentage =
    payload.monthly_income > 0
      ? (payload.rent /
          payload.monthly_income) *
        100
      : 0;

  const spendingAlerts: string[] = [];
  const savingsSuggestions: string[] =
    [];

  if (rentPercentage > 40) {
    spendingAlerts.push(
      "Your rent is above 40% of your monthly income, which may put pressure on other essential expenses."
    );
  }

  if (
    totalExpenses >
    payload.monthly_budget
  ) {
    spendingAlerts.push(
      "Your estimated expenses exceed the monthly budget you entered."
    );
  }

  if (remainingAmount < 0) {
    spendingAlerts.push(
      "Your planned expenses are higher than your monthly income."
    );
  }

  if (
    payload.savings <
    payload.monthly_income * 0.1
  ) {
    savingsSuggestions.push(
      "Try to reserve at least 10% of your monthly income for savings."
    );
  }

  savingsSuggestions.push(
    "Keep a separate emergency fund for deposits, medical needs, and unexpected relocation costs."
  );

  savingsSuggestions.push(
    "Compare shared housing options if rent is reducing your ability to save."
  );

  return {
    advice:
      remainingAmount >= 0
        ? `Your plan leaves approximately ₹${remainingAmount.toLocaleString(
            "en-IN"
          )} after monthly expenses. Focus on maintaining an emergency reserve and keeping rent proportionate to income.`
        : `Your plan exceeds your monthly income by approximately ₹${Math.abs(
            remainingAmount
          ).toLocaleString(
            "en-IN"
          )}. Reduce non-essential expenses or consider a more affordable housing option.`,
    total_expenses: totalExpenses,
    remaining_amount: remainingAmount,
    savings_rate: savingsRate,
    spending_alerts: spendingAlerts,
    savings_suggestions:
      savingsSuggestions,
  };
}

export async function mockGetPersonalizedSuggestions(): Promise<PersonalizedSuggestionsResponse> {
  await delay(850);

  return {
    suggestions: [
      {
        id: "suggestion-1",
        type: "budget",
        title:
          "Review your rent-to-budget ratio",
        description:
          "Try to keep rent within 30–40% of your monthly income to leave room for food, travel, utilities, and savings.",
        action_label:
          "Open Budget Advisor",
        action_url:
          "/budget-advisor",
      },
      {
        id: "suggestion-2",
        type: "housing",
        title:
          "Compare verified housing listings",
        description:
          "Prioritise verified properties with clear rent, deposit, ownership, and availability details.",
        action_label:
          "Browse Housing",
        action_url: "/housing",
      },
      {
        id: "suggestion-3",
        type: "safety",
        title:
          "Check suspicious listings before paying",
        description:
          "Use the scam checker whenever a listing demands urgent payment or avoids an in-person property visit.",
        action_label:
          "Check a Listing",
        action_url:
          "/scam-check",
      },
      {
        id: "suggestion-4",
        type: "transport",
        title:
          "Include commute cost in locality decisions",
        description:
          "A cheaper room may become expensive if daily travel takes too long or requires multiple transport changes.",
        action_label:
          "Find Localities",
        action_url:
          "/locality",
      },
    ],
  };
}