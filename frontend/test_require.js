
try {
    console.log('Resolving tailwindcss...');
    const path = require.resolve('tailwindcss');
    console.log('tailwindcss found at:', path);
} catch (e) {
    console.error('Error resolving tailwindcss:', e.message);
}
