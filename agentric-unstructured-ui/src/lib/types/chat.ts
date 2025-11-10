export type Chat = {
	id: string;
	title: string;
	request_id: string;
	created_at: string;
	updated_at: string;
	chatMessages: ChatMessage[];
};
export type MessageType = 'text' | 'tool_result' | 'tool_call';

export interface ChatMessage {
	id: string;
	role: AgentRole;
	type: MessageType;
	message: string;
	created_at: string;
	updated_at: string;
}

export enum AgentRole {
	USER = 'user_agent',
	ZURICH_REQUEST_AGENT = 'insurance_request_agent',
	ZURICH_ANALYST_AGENT = 'insurance_analyst_agent',
	ZURICH_GENERAL_AGENT = 'zurich_general_agent',
	ZURICH_EMAIL_AGENT = 'email_preparation_agent',
	ZURICH_CLAIM_AGENT = 'claim_assistant_agent'
}

export enum MesgType {
	'text',
	'tool_call',
	'tool_result',
	'MISSING_EMAIL',
	'DECLINE_EMAIL'
}

// type: MesgType;
// role: Role;
export type StreamChat = {
	message: string;
};
export type ConversationItem = {
	message: string | object[] | File[] | { file_name: string; file_size: string };
	role: string;
	is_thought_included?: boolean;
	thought?: string;
	type: string;
	loading?: boolean;
	displayType:
		| 'text'
		| 'table'
		| 'tool_call'
		| 'tool_result'
		| 'markdown'
		| 'button'
		| 'three-btns'
		| 'file'
		| 'upload'
		| 'file_show';
	time: string;
};
export type ClassiClassificationfication = {
	broker_commission: string;
	business_description: string;
	product_type: string;
	policy_start_date: string;
	policy_end_date: string;
	limit_section_1_material_damage: number;
	limit_section_2_business_interruption: number;
	limit_combined_section_number_and_2: number;
	sublimit_accidental_damage: string;
	sublimit_burglary_theft: string;
	deductible_section_number_losses: number;
	deductible_section_2_losses: number;
	deductible_combined_losses: number;
	risk_building_value: number;
	risk_contents_value: number;
	risk_construction_wall: string;
	risk_construction_roof: string;
	risk_construction_floor: string;
	risk_construction_frame: string;
	risk_year_built: number;
	risk_fire_protection: string;
	risk_security: string;
	risk_sprinkler_effectiveness: string;
	risk_fire_alarm_effectiveness: string;
	risk_occupancy: string;
	risk_number_of_storeys: string;
};

export type PolicyStatisticData = {
	highlevel_info: {
		premium_amount: number;
		coverage_amount: number;
		deductible_amounts: Record<string, unknown>;
	};
	policy_detail: {
		broker_name: string;
		insured_name: string;
		inception_date: string; // ISO date
		expiry_date: string; // ISO date
		segment: string;
	};
	risk: {
		property_addresses: {
			property_construction_details: {
				building: number;
				contents_stock_in_trade: number;
				construction_wall: string;
				construction_roof: string;
				construction_floor: string;
				construction_frame: string;
				construction_year_built: number;
				fire_protection: string;
				security: string;
				sprinkler_effectiveness: string;
				fire_alarm_effectiveness: string;
				occupancy: string;
				number_of_storeys: string;
			};
			location_coverage: {
				limit_of_liability: number;
				accidental_damage: string;
				burglary_theft: string;
			};
		};
	};
	policy_coverage: {
		section_1_material_loss_or_damage: number;
		section_2_consequential_loss_business_interruption: number;
		combined_limit: number;
		insurer_share: number;
	};
	quote_summary: {
		risk_score: string;
		premium_amount: number;
		premium_description: string;
		coverage_amount: number;
		policy_coverage_narrative: string;
	};
};
