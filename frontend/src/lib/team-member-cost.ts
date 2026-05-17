import type { SocialChargesConfig, TeamMember } from '@/types/admin';

/** Monthly gross salary including org social charges when enabled for this member (display / admin table). */
export function getTeamMemberSalaryWithCharges(
    member: TeamMember,
    socialCharges: SocialChargesConfig
): number {
    const chargesMult =
        member.applySocialCharges && socialCharges.enable_social_charges
            ? 1 + (socialCharges.total_percentage || 0) / 100
            : 1;
    return member.salaryMonthlyBrute * chargesMult;
}
