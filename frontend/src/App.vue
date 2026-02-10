<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getDashboardData } from './services/api';
import { 
  TrendingUp, 
  ShoppingBag, 
  Package, 
  AlertTriangle, 
  DollarSign,
  Truck,
  MapPin
} from 'lucide-vue-next';

// Data State
const dashboardData = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    dashboardData.value = await getDashboardData();
  } catch (err) {
    error.value = "Failed to load dashboard data. Ensure the backend is running.";
  } finally {
    loading.value = false;
  }
});

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

const formatNumber = (value: number) => {
  return new Intl.NumberFormat('en-US').format(value);
};
</script>

<template>
  <div class="min-h-screen p-6 lg:p-10 text-white selection:bg-blue-500/30">
    <!-- Header -->
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
      <div>
        <h1 class="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          Supply Chain Dashboard
        </h1>
        <p class="text-slate-400 mt-2 text-lg">Real-time optimization and visibility</p>
      </div>
      <div v-if="dashboardData" class="flex items-center gap-3 px-4 py-2 glass-card">
        <div class="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
        <span class="text-slate-300 font-medium">System Live</span>
      </div>
    </header>

    <div v-if="loading" class="flex flex-col items-center justify-center h-[60vh]">
      <div class="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
      <p class="mt-4 text-slate-400 animate-pulse">Processing Supply Chain Data...</p>
    </div>

    <div v-else-if="error" class="glass-card p-10 text-center max-w-2xl mx-auto">
      <AlertTriangle class="w-16 h-16 text-rose-500 mx-auto mb-4" />
      <h2 class="text-2xl font-bold text-rose-400 mb-2">Analysis Error</h2>
      <p class="text-slate-400">{{ error }}</p>
      <button @click="window.location.reload()" class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl transition-all">
        Retry Connection
      </button>
    </div>

    <div v-else class="space-y-8 animate-in fade-in slide-in-from-bottom-5 duration-700">
      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="glass-card p-6 group hover:translate-y-[-4px] transition-all cursor-default">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-blue-500/10 rounded-xl text-blue-400 group-hover:scale-110 transition-transform">
              <DollarSign class="w-6 h-6" />
            </div>
          </div>
          <div class="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Revenue</div>
          <div class="text-3xl font-bold mt-1 text-white">{{ formatCurrency(dashboardData.summary.total_revenue) }}</div>
        </div>

        <div class="glass-card p-6 group hover:translate-y-[-4px] transition-all cursor-default">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-emerald-500/10 rounded-xl text-emerald-400 group-hover:scale-110 transition-transform">
              <ShoppingBag class="w-6 h-6" />
            </div>
          </div>
          <div class="text-slate-400 text-sm font-medium uppercase tracking-wider">Products Sold</div>
          <div class="text-3xl font-bold mt-1 text-white">{{ formatNumber(dashboardData.summary.total_sold) }}</div>
        </div>

        <div class="glass-card p-6 group hover:translate-y-[-4px] transition-all cursor-default">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-amber-500/10 rounded-xl text-amber-400 group-hover:scale-110 transition-transform">
              <Package class="w-6 h-6" />
            </div>
          </div>
          <div class="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Stock</div>
          <div class="text-3xl font-bold mt-1 text-white">{{ formatNumber(dashboardData.summary.total_stock) }}</div>
        </div>

        <div class="glass-card p-6 group hover:translate-y-[-4px] transition-all cursor-default">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-rose-500/10 rounded-xl text-rose-400 group-hover:scale-110 transition-transform">
              <AlertTriangle class="w-6 h-6" />
            </div>
          </div>
          <div class="text-slate-400 text-sm font-medium uppercase tracking-wider">Avg Defect Rate</div>
          <div class="text-3xl font-bold mt-1 text-white text-rose-400">{{ dashboardData.summary.avg_defect_rate }}%</div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Revenue by Type -->
        <div class="glass-card p-8 lg:col-span-1">
          <h3 class="text-xl font-bold mb-6 flex items-center gap-2 text-slate-200">
             <TrendingUp class="w-5 h-5 text-blue-400" /> Revenue Distribution
          </h3>
          <div class="space-y-6">
            <div v-for="type in dashboardData.product_types" :key="type['Product type']" class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-slate-300 font-medium capitalize">{{ type['Product type'] }}</span>
                <span class="text-blue-400">{{ formatCurrency(type['Revenue generated']) }}</span>
              </div>
              <div class="h-3 bg-white/5 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-blue-600 to-blue-400" 
                     :style="{ width: `${(type['Revenue generated'] / dashboardData.summary.total_revenue) * 100}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Inventory Heatmap / Critical SKU Table -->
        <div class="glass-card p-8 lg:col-span-2 overflow-x-auto">
          <h3 class="text-xl font-bold mb-6 flex items-center gap-2 text-slate-200">
             <MapPin class="w-5 h-5 text-emerald-400" /> Critical SKUs (ABC Class A)
          </h3>
          <table class="w-full text-left">
            <thead>
              <tr class="text-slate-500 border-b border-white/5 uppercase text-xs tracking-widest">
                <th class="pb-3 px-2">SKU</th>
                <th class="pb-3 px-2">Type</th>
                <th class="pb-3 px-2">Stock</th>
                <th class="pb-3 px-2">Sales</th>
                <th class="pb-3 px-2">Revenue</th>
                <th class="pb-3 px-2">ABC</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5">
              <tr v-for="item in dashboardData.inventory.filter((i:any) => i.ABC_Class === 'A').slice(0, 8)" :key="item.SKU" 
                  class="group hover:bg-white/5 transition-colors cursor-default">
                <td class="py-4 px-2 font-mono text-blue-400 group-hover:text-blue-300">{{ item.SKU }}</td>
                <td class="py-4 px-2 text-slate-300 capitalize text-sm">{{ item['Product type'] }}</td>
                <td class="py-4 px-2 font-medium">{{ item['Stock levels'] }}</td>
                <td class="py-4 px-2 font-medium">{{ item['Number of products sold'] }}</td>
                <td class="py-4 px-2 text-emerald-400 font-semibold">{{ formatCurrency(item['Revenue generated']) }}</td>
                <td class="py-4 px-2">
                  <span class="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-lg font-bold">Class A</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Logistics Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="glass-card p-8">
           <h3 class="text-xl font-bold mb-6 flex items-center gap-2 text-slate-200">
             <Truck class="w-5 h-5 text-amber-400" /> Shipping Carrier Efficiency
          </h3>
          <div class="grid grid-cols-1 gap-4">
            <div v-for="ship in dashboardData.shipping.slice(0, 5)" :key="ship['Shipping carriers'] + ship['Transportation modes']" 
                 class="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-all">
              <div class="flex justify-between items-center">
                <div>
                  <div class="text-slate-200 font-bold uppercase text-xs tracking-wider">{{ ship['Shipping carriers'] }}</div>
                  <div class="text-slate-400 text-sm">{{ ship['Transportation modes'] }}</div>
                </div>
                <div class="text-right">
                  <div class="text-amber-400 font-bold">{{ formatCurrency(ship['Shipping costs']) }}</div>
                  <div class="text-[10px] text-slate-500 uppercase">Avg Cost</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-panel p-10 flex flex-col items-center justify-center text-center border-dashed border-2">
          <p class="text-slate-500 max-w-xs italic">
            "Supply chain visualization is about connecting the dots between production costs and customer satisfaction."
          </p>
          <div class="mt-8 flex gap-4">
             <div class="w-24 h-1 bg-blue-500/50 rounded-full"></div>
             <div class="w-8 h-1 bg-emerald-500/50 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.glass-card {
  @apply bg-white bg-opacity-[0.03] backdrop-blur-xl border border-white border-opacity-[0.08] rounded-[2rem] shadow-2xl;
}

.glass-panel {
  @apply bg-black bg-opacity-20 backdrop-blur-md border border-white border-opacity-5 rounded-[2.5rem];
}
</style>
