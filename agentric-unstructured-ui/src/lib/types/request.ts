export enum RequestSubmissionStatus {
	PROCESSING = 'PROCESSING',
	INREVIEW = 'IN_REVIEW',
	CLOSED = 'CLOSED',
	ERROR = 'ERROR'
}

export enum APPETITESTATUS {
	APPROVED = 'APPROVED',
	DECLINED = 'DECLINED',
	PENDING = 'PENDING',
	DUPLICATE = 'DUPLICATE',
	DECIDING = 'DECIDING',
	PARTIAL_PAYMENT = 'PARTIAL_PAYMENT',
	MISSING = 'MISSING',
	PAID = 'PAID'
}

export type ClaimResponse = {
	request_id: string;
	message: string;
};
export type Request = {
	id: string;
	request_number: string;
	status: APPETITESTATUS;
	submission_status: RequestSubmissionStatus;
	created_at: string;
	updated_at: string;

	// System fields
	missing_documents: string[] | null;
	is_medical_claim: boolean;
	hashed_code: string | null;
	decision_reason: string | null;
	payment_status: string | null;
	payment_reason: string | null;

	// Claim Info (money fields as number | null)
	claim_number: string | null;
	approved_amount: number | null; // Decimal -> number
	claim_amount: number | null; // Decimal -> number
	type_of_claim: string | null;
	requested_reimbursement_amount: number | null; // Decimal -> number
	insurance_agency_name: string | null;
	premium_amount: number | null; // Decimal -> number

	// Trip Info
	trip_start_date: string | null; // ISO date-time
	trip_end_date: string | null;
	trip_cost: string | null; // ISO date-time
	destination: string | null;

	// Client Info
	client_name: string | null;
	client_email_address: string | null;
	client_phone_number: string | null;
	client_post_code: string | null;
	description: string | null;

	// Policy Info
	policy_holder: string | null;
	policy_number: string | null;
	policy_effective_date: string | null; // ISO date-time
	policy_expiration_date: string | null; // ISO date-time
	coverage_limits: number | null; // Decimal -> number
	maximum_coverage_amount: number | null; // Decimal -> number

	// Broker Info
	broker_name: string | null;
	broker_email: string | null;
	broker_commission: number | null;
	unique_identifier: string | null;
	created_by: string | null;
};

export type PaginatedData<T> = {
	items: T[];
	limit: number;
	total: number;
	offset: number;
	hasNextPage?: boolean;
};

export type Classification = {
	broker_name: string;
	broker_commission: string;
	product_type: string;
	policy_start_date: string;
	policy_end_date: string;
	buildings: number;
	construction_wall: string;
	construction_roof: string;
	construction_floor: string;
	construction_frame: string;
	construction_year_built: number;
	security: string;
	sprinkler_effectiveness: string;
	fire_alarm_effectiveness: string;
	occupancy: string;
	number_of_storeys: string;
	fire_protection: string;
	section_1_material_damage: number;
	section_2_consequential_loss_business_interruption: number;
	combined_section_1_and_2: number;
	accidental_damage: number;
	blurglary_theft_of_property: number;
	all_other_losses_section1: number;
	all_other_losses_section2: number;
	all_other_losses_section1_2_combined: number;
	burglary_theft_of_property: string | number;
	combined_section_1_and_2_deductible: number;
	contents_stock_in_trade: number;

	// customer_name: str
	// customer_address: str
	// lob: str
	// effectivity_date: datetime
	// broker_name: Optional[str]
	// broker_commission: Optional[str]
	// product_type: Optional[str]
	// policy_start_date: Optional[datetime]
	// policy_end_date: Optional[datetime]

	// business_description: Optional[str]
	// buildings: Optional[int]
	// construction_wall: Optional[str]
	// construction_roof: Optional[str]
	// construction_floor: Optional[str]
	// construction_frame: Optional[str]
	// construction_year_built: Optional[int]
	// security: Optional[str]
	// sprinkler_effectiveness: Optional[str]
	// fire_alarm_effectiveness: Optional[str]
	// occupancy: Optional[str]
	// number_of_storeys: Optional[str]

	// fire_protection: Optional[str]

	// section_1_material_damage: Optional[int]
	// section_2_consequential_loss_business_interruption: Optional[int]
	// combined_section_1_and_2: Optional[int]

	// accidental_damage: Optional[Union[int, str]]
	// burglary_theft_of_property: Optional[Union[int, str]]

	// all_other_losses_section1: Optional[int]
	// all_other_losses_section2: Optional[int]

	// combined_section_1_and_2_deductible: Optional[int]
	// contents_stock_in_trade: Optional[int]
};

export type RiskInfo = {
	risk_score: number;
	risk_factors: Record<string, unknown>;
};
export type AppetiteInfo = {
	appetite_score: 40;
	in_appetite_industries: Record<string, unknown>;
	appetite_score_factor: Record<string, unknown>;
};

export type DeclineValues = {
	decline_reason: string;
	is_single_location: boolean;
	decline_rules: {
		backdating: DeclinedDescriptionType;
		customer_address: DeclinedDescriptionType;
		customer_name: DeclinedDescriptionType;
		knockout_postcodes: DeclinedDescriptionType;
		low_value: DeclinedDescriptionType;
		wood_construction: DeclinedDescriptionType;
	};
};

export type DeclinedDescriptionType = {
	pass: boolean;
	value: string;
	criteria: string;
};

export type CoverageRecommendation = {
	limit_of_liability: string;
	accidental_damage: string;
	burglary_theft: string;
};

export type CoverageItem = {
	peril: string;
	covered: string;
	section: string;
	deductible_section: string;
	deductible_pd_both_basis: string;
	deductible_pd_both_minimum: number | null;
	deductible_pd_both_maximum: number | null;
	deductible_pd_both_value: number | null;
	deductible_bi_basis: string | null;
	deductible_bi_minimum: number | null;
	deductible_bi_maximum: number | null;
	deductible_bi_value: number | null;
	sublimit_type: string;
	sublimit_basis: string;
	sublimit_value: number | null;
};
