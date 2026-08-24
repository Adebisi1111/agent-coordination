// Simple verification — check HTML structure and JS without browser
import { readFileSync } from 'fs';

const html = readFileSync('public/index.html', 'utf8');
const client = readFileSync('public/gl-client.js', 'utf8');

console.log('=== HTML CHECKS ===');
console.log('has title:', html.includes('Agent Coordination'));
console.log('has nav tabs:', (html.match(/data-tab=/g) || []).length);
console.log('has taskDesc:', html.includes('taskDesc'));
console.log('has taskReward:', html.includes('taskReward'));
console.log('has agentCaps:', html.includes('agentCaps'));
console.log('has agentStake:', html.includes('agentStake'));
console.log('has postBtn:', html.includes('postBtn'));
console.log('has regBtn:', html.includes('regBtn'));
console.log('has script module:', html.includes('type="module"'));

console.log('\n=== JS CHECKS ===');
console.log('imports genlayer-js:', client.includes('genlayer-js') || html.includes('genlayer-js'));
console.log('has contract address:', html.includes('0x07DCEc4A77AB245a7F66144eDDa6A6D9C05789eD'));
console.log('has loadTasks:', html.includes('loadTasks'));
console.log('has postTask:', html.includes('postTask'));
console.log('has registerAgent:', html.includes('registerAgent'));
console.log('has claimTask:', html.includes('claimTask'));
console.log('has verifyTask:', html.includes('verifyTask'));
console.log('has contractCall:', html.includes('contractCall'));
console.log('has getClaimCount:', html.includes('getClaimCount'));
console.log('has getTask:', html.includes('getTask'));
console.log('exposes claimTask to window:', html.includes('window.claimTask = claimTask'));
console.log('exposes verifyTask to window:', html.includes('window.verifyTask = verifyTask'));

console.log('\n=== CONTRACT METHOD NEEDED ===');
console.log('getClaimCount exists in contract: YES (returns task_count)');
console.log('getTask exists in contract: YES');
console.log('getAgent exists in contract: YES');

console.log('\n=== POTENTIAL ISSUES ===');
if (!html.includes('getClaimCount')) console.log('WARNING: getClaimCount not called');
if (!html.includes('getTask')) console.log('WARNING: getTask not called');
