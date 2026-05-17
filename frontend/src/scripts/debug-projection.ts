
import { breakEvenService } from '../services/breakEvenService';
import { MOCK_BREAK_EVEN_DATA } from '../data/mock-break-even';

async function runDebug() {
    console.log("--- Debugging Projection Logic ---");
    console.log("Base Allocated:", MOCK_BREAK_EVEN_DATA.current_allocated_hours);
    console.log("Break Even Target:", MOCK_BREAK_EVEN_DATA.break_even_hours);

    // Test Case 1: 0% Growth
    console.log("\nTest Case 1: 0% Growth, 12 Months");
    const result0 = await breakEvenService.generateProjection(MOCK_BREAK_EVEN_DATA, 12, 0);
    console.log("Month 1 Allocated:", result0.projection[0].allocated_hours);
    console.log("Month 12 Allocated:", result0.projection[11].allocated_hours);
    console.log("Break Even Date:", result0.break_even_date);

    // Test Case 2: 5% Growth
    console.log("\nTest Case 2: 5% Growth, 12 Months");
    const result5 = await breakEvenService.generateProjection(MOCK_BREAK_EVEN_DATA, 12, 5);
    console.log("Month 1 Allocated:", result5.projection[0].allocated_hours);
    console.log("Month 12 Allocated:", result5.projection[11].allocated_hours);
    console.log("Break Even Date:", result5.break_even_date);

    // Verify compound logic
    // Month 1 should be Base * 1.05
    const expectedM1 = MOCK_BREAK_EVEN_DATA.current_allocated_hours * 1.05;
    console.log("Expected Month 1:", expectedM1);
    console.log("Actual Month 1:", result5.projection[0].allocated_hours);
}

runDebug();
