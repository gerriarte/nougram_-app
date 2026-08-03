
export type PricingType = 'hourly' | 'fixed' | 'recurring' | 'project_value';

export interface Service {
    id: number;
    name: string;
    description?: string;
    pricingType: PricingType;
    defaultMarginTarget: number; // 0.40
    isActive: boolean;
}

export interface QuoteItem {
    id: string; // Temporary UI ID
    serviceId: number;
    serviceName: string; // Título del ítem — obligatorio en el builder
    description?: string; // Alcance del ítem — obligatorio en el builder, persistido con la cotización

    // Inputs (Union based on PricingType)
    pricingType: PricingType;
    estimatedHours?: number; // Hourly
    fixedPrice?: number;     // Fixed (Treated as Base Cost in spec 2.1.2)
    quantity: number;        // Default 1
    recurringPrice?: number; // Recurring
    billingFrequency?: 'monthly' | 'annual';
    durationMonths?: number; // New: For recurring services
    allocations?: import('./quote-builder').ResourceAllocation[]; // New: Per-item resource allocations
    teamAssignment?: import('./quote-builder').TeamAssignment;
    projectValue?: number;   // Project Value (Selling Price)

    // Calculated Real-time
    internalCost: number;
    clientPrice: number;
    marginPercentage: number;

    // Overrides
    manualPrice?: number; // If user overrides the calculated price
}

export interface TaxConfig {
    id: number;
    name: string;
    code?: string;
    percentage: number; // 19.0
    country?: string;
    description?: string;
    isActive?: boolean;
}

export interface ResourceAllocation {
    id: string; // Temporary UI ID
    teamMemberId: number;
    hours: number;
    role?: string;
    startDate?: string; // ISO Date YYYY-MM-DD
    endDate?: string;   // ISO Date YYYY-MM-DD
    notes?: string;
}

export interface TeamAssignment {
    id?: number;
    cellId: number;
    cellVersionId?: number;
    occupancyPercentage: number;
    durationMonths?: number;
}

export interface TeamMemberMock {
    id: number;
    name: string;
    role: string;
    availableHours: number;
    avatarUrl?: string; // Optional for UI
}

export interface Contingency {
    description: string;
    type: 'fixed' | 'percentage';
    value: number;
}

export interface Vendor {
    id: number;
    name: string;
    description?: string;
    category?: string;
    defaultCost?: number;
    defaultMarkupPercentage?: number;
    isActive: boolean;
}

export interface QuoteExpense {
    id: string;           // Temporary UI ID
    name: string;
    vendorName?: string;
    vendorId?: number;    // FK to Vendor catalog (optional)
    cost: number;
    markupPercentage: number; // 0.10 = 10%
    quantity: number;
    category: string;
    clientPrice: number;  // cost × quantity × (1 + markup) — computed by backend
}

export interface QuoteBuilderState {
    step: 'editor' | 'preview';
    id?: string; // Track the ID of the quote being edited
    version?: number; // Track current version

    // Project Info
    projectName: string;
    clientId?: number | null;
    clientName: string;
    clientCompany?: string;
    clientRequester?: string;
    clientEmail: string;
    projectType?: string;
    projectDescription?: string;
    currency: 'COP' | 'USD' | 'EUR' | 'ARS' | 'PEN' | 'MXN';

    // Items
    items: QuoteItem[];

    // Vendor / pass-through expenses
    expenses: QuoteExpense[];

    // Config
    targetMargin: number; // 0.35
    selectedTaxIds: number[];
    contingency?: Contingency; // New: Contingency Module

    // Resource Allocation
    showResourceAllocation: boolean;
    resourceAllocations: ResourceAllocation[];

    // Validation
    allowLowMargin: boolean;

    // Public Proposal
    publicToken?: string;
    tokenExpiresAt?: string;
    viewCount?: number;
    lastViewedAt?: string;
}

export interface CalculationSummary {
    totalInternalCost: number;
    totalClientPrice: number; // Before Tax
    totalTaxes: number;
    totalWithTaxes: number;
    netMarginAmount: number;
    netMarginPercent: number;
    realIncome: number;

    // Expense breakdown (internal cost vs client price from vendor expenses)
    expensesInternalCost: number;
    expensesClientPrice: number;

    // Contingency Results
    contingencyAmount: number;
    contingencyTotal: number; // Price + Contingency
    // Wait. If I bill $20M + $3.8M VAT = $23.8M.
    // I receive $23.8M. I pay $3.8M to Gov. I have $20M left.
    // BUT Spec 5.6 example:
    // Price Client (before tax): $20M.
    // Taxes: $4.692M (IVA + ICA + Rete).
    // Total with Taxes: $24.692M.
    // "Ingreso Real (después de impuestos): $15.308.000".
    // This means $20M - $4.692M = $15.308M.
    // THIS IS WRONG ACCOUNTING usually. VAT is added on top. ReteFuente is subtracted from payment.
    // ICA is a cost.
    // However, spec 4.3 example shows "Ingreso Real" subtracts ALL taxes from the "Precio Cliente BEFORE Tax"?
    // "Precio Cliente (antes): 20M".
    // "Total Impuestos: 4.69M".
    // "Ingreso Real: 15.3M".
    // This implies the user treats "Precio Cliente" as the gross amount, but then loses money to taxes?
    // OR does it mean ReteFuente (withheld) + IVA (paid) + ICA (paid) reduces cash flow?
    // Let's STICK TO THE SPEC EXAMPLE for the math, even if accounting-wise it's specific to this User's mental model.
    // "Ingreso Real = Precio Cliente (Antes Impuestos) - Total Impuestos"?
    // Wait, looking at the layout: 
    // "Precio Cliente (con impuestos): 24.692.000".
    // "Ingreso Real": 15.308.000.
    // 24.692 - 15.308 = 9.384. That's approx double taxes?
    // Let's check the Math in Spec 4.3 strictly:
    // $20,000,000 (Base)
    // Taxes = 3.8 + 0.192 + 0.7 = 4.692.
    // $20M - 4.692M = 15.308M.
    // YES. The spec logic is: Real Income = Base Price - Taxes.
    // This implies the user sets a Base Price, adds Taxes on top (to bill client), BUT considers those taxes as "Lost" from the base? 
    // No, usually VAT is Neutral. 
    // But ReteFuente is withheld. 
    // Maybe the "Total Impuestos" line in the example sums up everything the user *feels* they lose?
    // "Ingreso Real" suggests Liquidity.
    // I will implement the math exactly as: `realIncome = basePrice - totalTaxes`.
}
