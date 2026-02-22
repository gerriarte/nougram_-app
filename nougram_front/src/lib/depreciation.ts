
import { Equipment, DepreciationResult } from '@/types/equipment';

/**
 * Calculates current status and depreciation metrics for an asset.
 */
export function calculateDepreciation(equipment: Equipment): DepreciationResult {
    const {
        purchasePrice, salvageValue, usefulLifeMonths,
        purchaseDate, depreciationMethod, currency, exchangeRateAtPurchase
    } = equipment;

    // 1. Normalize Cost to Base Currency (COP usually)
    let purchasePriceNative = purchasePrice;
    let salvageValueNative = salvageValue;

    if (currency !== 'COP' && exchangeRateAtPurchase) {
        purchasePriceNative = purchasePrice * exchangeRateAtPurchase;
        salvageValueNative = salvageValue * exchangeRateAtPurchase;
    }

    // 2. Calculate Base
    const depreciableBase = purchasePriceNative - salvageValueNative;

    // 3. Time Calculations
    const start = new Date(purchaseDate);
    const now = new Date();

    // Months passed = (YearDiff * 12) + MonthDiff
    let monthsPassed = (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth());

    // Cap months passed at useful life (cannot depreciate more than life for straight line usually, unless usage based)
    // But logically, if it's older than life, it's fully depreciated.
    if (monthsPassed > usefulLifeMonths) monthsPassed = usefulLifeMonths;
    if (monthsPassed < 0) monthsPassed = 0; // Future purchase

    const monthsRemaining = Math.max(0, usefulLifeMonths - monthsPassed);

    // 4. Algorithm
    let monthlyDepreciation = 0;
    let totalDepreciated = 0;
    let currentBookValue = purchasePriceNative;

    if (depreciationMethod === 'straight_line') {
        // Straight Line: Constant monthly cost
        monthlyDepreciation = depreciableBase / usefulLifeMonths;
        totalDepreciated = monthlyDepreciation * monthsPassed;
    }
    else if (depreciationMethod === 'declining_balance') {
        // Double Declining Balance
        // Rate per month = (2 / LifeInMonths)
        // This is complex because it varies month to month. 
        // For "Current Status", we ideally need to iterate or use formula.
        // Iteration is safer for exactness.

        let bookVal = purchasePriceNative;
        const monthlyRate = (2 / usefulLifeMonths);

        for (let i = 0; i < monthsPassed; i++) {
            let dep = bookVal * monthlyRate;
            // Cap at salvage value
            if ((bookVal - dep) < salvageValueNative) {
                dep = bookVal - salvageValueNative;
            }
            bookVal -= dep;
            totalDepreciated += dep;
        }

        currentBookValue = bookVal;

        // "Current" Monthly Depreciation (projected for NEXT month)
        // If already at salvage, 0. Else, calc next step.
        if (currentBookValue <= salvageValueNative) {
            monthlyDepreciation = 0;
        } else {
            monthlyDepreciation = currentBookValue * monthlyRate;
            if ((currentBookValue - monthlyDepreciation) < salvageValueNative) {
                monthlyDepreciation = currentBookValue - salvageValueNative;
            }
        }
    }

    // Final Constraints
    if (totalDepreciated > depreciableBase) totalDepreciated = depreciableBase;
    currentBookValue = purchasePriceNative - totalDepreciated;

    // Percentage
    const percentageDepreciated = (totalDepreciated / depreciableBase) * 100;
    const isFullyDepreciated = totalDepreciated >= depreciableBase;

    return {
        monthlyDepreciation,
        currentBookValue,
        totalDepreciated,
        percentageDepreciated,
        monthsRemaining,
        isFullyDepreciated
    };
}
