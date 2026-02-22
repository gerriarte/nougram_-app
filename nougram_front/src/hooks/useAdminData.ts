import { useState, useEffect, useCallback } from 'react';
import {
    TeamMemberInput,
    SocialChargesConfig,
    FixedCostInput,
    GlobalConfig
} from "@/types/admin";
import { adminService } from '@/services/adminService';

export function useAdminData() {
    const [isLoading, setIsLoading] = useState(true);

    // Data State
    const [members, setMembers] = useState<TeamMemberInput[]>([]);
    const [fixedCosts, setFixedCosts] = useState<FixedCostInput[]>([]);
    const [socialConfig, setSocialConfig] = useState<SocialChargesConfig>(adminService.getSocialConfig()); // Initialize with defaults/sync if possible, but effect handles async illusion
    const [globalConfig, setGlobalConfig] = useState<GlobalConfig>(adminService.getGlobalConfig());

    // Load Data on Mount
    useEffect(() => {
        setIsLoading(true);
        // Simulate minor async to ensure hydration matches
        const m = adminService.getMembers();
        const c = adminService.getCosts();
        const s = adminService.getSocialConfig();
        const g = adminService.getGlobalConfig();

        setMembers(m);
        setFixedCosts(c);
        setSocialConfig(s);
        setGlobalConfig(g);
        setIsLoading(false);
    }, []);

    // --- UPDATERS (Sync state + Storage) ---

    // Members
    const updateMembers = (newMembers: TeamMemberInput[]) => {
        setMembers(newMembers);
        adminService.saveMembers(newMembers);
    };

    const addMember = (member: TeamMemberInput) => {
        const newMember = { ...member, id: Date.now() };
        const updated = [...members, newMember];
        updateMembers(updated);
    };

    const editMember = (member: TeamMemberInput) => {
        const updated = members.map(m => m.id === member.id ? member : m);
        updateMembers(updated);
    };

    const deleteMember = (id: number) => {
        const updated = members.filter(m => m.id !== id);
        updateMembers(updated);
    };

    // Costs
    const updateCosts = (newCosts: FixedCostInput[]) => {
        setFixedCosts(newCosts);
        adminService.saveCosts(newCosts);
    };

    const addCost = (cost: FixedCostInput) => {
        const newCost = { ...cost, id: Date.now() };
        const updated = [...fixedCosts, newCost];
        updateCosts(updated);
    };

    const editCost = (cost: FixedCostInput) => {
        const updated = fixedCosts.map(c => c.id === cost.id ? cost : c);
        updateCosts(updated);
    };

    const deleteCost = (id: number) => {
        const updated = fixedCosts.filter(c => c.id !== id);
        updateCosts(updated);
    };

    // Configs
    const updateSocialConfig = (config: SocialChargesConfig) => {
        setSocialConfig(config);
        adminService.saveSocialConfig(config);
    };

    const updateGlobalConfig = (config: GlobalConfig) => {
        setGlobalConfig(config);
        adminService.saveGlobalConfig(config);
    };

    const resetData = () => {
        const defaults = adminService.resetDefaults();
        setMembers(defaults.members);
        setFixedCosts(defaults.costs);
        setSocialConfig(defaults.social);
        setGlobalConfig(defaults.global);
    };

    return {
        isLoading,
        members,
        fixedCosts,
        socialConfig,
        globalConfig,
        actions: {
            addMember,
            editMember,
            deleteMember,
            addCost,
            editCost,
            deleteCost,
            updateSocialConfig,
            updateGlobalConfig,
            resetData
        }
    };
}
