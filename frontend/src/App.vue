<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { getDashboardData } from './services/api';
import { 
  TrendingUp, 
  ShoppingBag, 
  Package, 
  AlertTriangle, 
  DollarSign,
  MapPin,
  Filter,
  Globe
} from 'lucide-vue-next';
import { 
  Chart as ChartJS, 
  Title, 
  Tooltip, 
  Legend, 
  BarElement, 
  CategoryScale, 
  LinearScale, 
  ArcElement, 
  PointElement, 
  LineElement 
} from 'chart.js';
import { Bar, Doughnut } from 'vue-chartjs';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import * as XLSX from 'xlsx';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement, PointElement, LineElement);

// Map Coordinates for Indian Cities
const CITY_COORDS: Record<string, [number, number]> = {
  'Mumbai': [19.0760, 72.8777],
  'Delhi': [28.6139, 77.2090],
  'Kolkata': [22.5726, 88.3639],
  'Bangalore': [12.9716, 77.5946],
  'Chennai': [13.0827, 80.2707]
};

// Data State
const originalData = ref<any>(null);
const dashboardData = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// Filters State
const selectedCategory = ref('Tous');
const selectedLocation = ref('Toutes');
const categories = ref<string[]>(['Tous']);
const locations = ref<string[]>(['Toutes']);

// Map Instance
let map: any = null;
const mapContainer = ref<HTMLElement | null>(null);
const markers = ref<any[]>([]);

onMounted(async () => {
  try {
    const data = await getDashboardData();
    originalData.value = data;
    dashboardData.value = JSON.parse(JSON.stringify(data));
    
    const raw = data.raw_data;
    categories.value = ['Tous', ...Array.from<string>(new Set(raw.map((item: any) => item['Product type'] as string)))];
    locations.value = ['Toutes', ...Array.from<string>(new Set(raw.map((item: any) => item['Location'] as string)))];
    
    // Initialize Map after DOM is ready
    setTimeout(() => initMap(), 100);
    
  } catch (err) {
    error.value = "Échec du chargement des données. Assurez-vous que le backend est lancé.";
  } finally {
    loading.value = false;
  }
});

const initMap = () => {
  if (!mapContainer.value) return;
  
  map = L.map(mapContainer.value).setView([20.5937, 78.9629], 4); // Center of India
  
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  updateMapMarkers();
};

const updateMapMarkers = () => {
  if (!map || !dashboardData.value) return;
  
  // Clear old markers
  markers.value.forEach(m => m.remove());
  markers.value = [];

  dashboardData.value.location_data.forEach((loc: any) => {
    const coords = CITY_COORDS[loc.Location];
    if (coords) {
      const marker = L.circleMarker(coords, {
        radius: Math.sqrt(loc['Revenue generated']) / 20,
        fillColor: '#3b82f6',
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.6
      }).addTo(map);

      marker.bindPopup(`
        <div class="p-2 text-slate-900">
          <div class="font-black uppercase text-xs mb-1">${loc.Location}</div>
          <div class="text-xs font-bold text-blue-600">Revenu: ${formatCurrency(loc['Revenue generated'])}</div>
          <div class="text-[10px] text-slate-500">Ventes: ${loc['Number of products sold']}</div>
        </div>
      `);
      
      markers.value.push(marker);
    }
  });
};

// Filtering Logic
watch([selectedCategory, selectedLocation], () => {
  if (!originalData.value) return;
  
  let filteredRaw = originalData.value.raw_data;
  
  if (selectedCategory.value !== 'Tous') {
    filteredRaw = filteredRaw.filter((item: any) => item['Product type'] === selectedCategory.value);
  }
  
  if (selectedLocation.value !== 'Toutes') {
    filteredRaw = filteredRaw.filter((item: any) => item['Location'] === selectedLocation.value);
  }
  
  // Recalculate Summary
  const revenue = filteredRaw.reduce((acc: number, item: any) => acc + item['Revenue generated'], 0);
  const sold = filteredRaw.reduce((acc: number, item: any) => acc + item['Number of products sold'], 0);
  const stock = filteredRaw.reduce((acc: number, item: any) => acc + item['Stock levels'], 0);
  const defect = filteredRaw.length > 0 ? filteredRaw.reduce((acc: number, item: any) => acc + item['Defect rates'], 0) / filteredRaw.length : 0;
  
  dashboardData.value.summary = {
    total_revenue: revenue,
    total_sold: sold,
    total_stock: stock,
    avg_defect_rate: defect.toFixed(2)
  };
  
  dashboardData.value.inventory = filteredRaw;
  
  // Update location data for markers
  const locData = locations.value.filter(l => l !== 'Toutes').map(l => {
    const cityItems = filteredRaw.filter((item: any) => item.Location === l);
    return {
      Location: l,
      'Revenue generated': cityItems.reduce((acc: number, i: any) => acc + i['Revenue generated'], 0),
      'Number of products sold': cityItems.reduce((acc: number, i: any) => acc + i['Number of products sold'], 0)
    };
  });
  
  dashboardData.value.location_data = locData;
  updateMapMarkers();

  // Zoom to selected location
  if (selectedLocation.value !== 'Toutes' && map) {
    const coords = CITY_COORDS[selectedLocation.value];
    if (coords) map.setView(coords, 7, { animate: true });
  } else if (map) {
    map.setView([20.5937, 78.9629], 4, { animate: true });
  }
});

const exportToPDF = () => {
  if (!dashboardData.value) return;
  const doc = new jsPDF();
  
  // Header
  doc.setFontSize(22);
  doc.setTextColor(59, 130, 246);
  doc.text('SUPPLY CHAIN PRO v4', 14, 20);
  
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139);
  doc.text(`Rapport d'Analyse Logistique - Généré le ${new Date().toLocaleString('fr-FR')}`, 14, 28);
  
  // Summary Stats
  doc.setFontSize(14);
  doc.setTextColor(30, 41, 59);
  doc.text('Résumé des Performances', 14, 40);
  
  doc.setFontSize(10);
  doc.text(`Chiffre d'Affaires Total: ${formatCurrency(dashboardData.value.summary.total_revenue)}`, 14, 48);
  doc.text(`Unités Vendues: ${formatNumber(dashboardData.value.summary.total_sold)}`, 14, 54);
  doc.text(`Taux de Défaut Moyen: ${dashboardData.value.summary.avg_defect_rate}%`, 14, 60);

  // Inventory Table
  const tableData = dashboardData.value.inventory.map((item: any) => [
    item.SKU,
    item['Product type'],
    item['Location'],
    item['Stock levels'],
    item['Number of products sold'],
    formatCurrency(item['Revenue generated'])
  ]);

  (doc as any).autoTable({
    startY: 70,
    head: [['SKU', 'Catégorie', 'Région', 'Stock', 'Ventes', 'Revenu']],
    body: tableData,
    theme: 'striped',
    headStyles: { fillColor: [59, 130, 246], fontStyle: 'bold' },
    styles: { fontSize: 8, cellPadding: 2 }
  });

  doc.save(`Rapport_Logistique_${selectedLocation.value}.pdf`);
};

const exportToExcel = () => {
  if (!dashboardData.value) return;
  
  // Prepare data for export
  const exportData = dashboardData.value.inventory.map((item: any) => ({
    'SKU': item.SKU,
    'Catégorie': item['Product type'],
    'Région': item['Location'],
    'Prix': item['Price'],
    'Ventes': item['Number of products sold'],
    'Revenu': item['Revenue generated'],
    'Stock': item['Stock levels'],
    'Plaintes Client': item['Customer demographics'],
    'Mode Transport': item['Transportation modes']
  }));

  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Données Logistiques');
  
  // Add a summary sheet
  const summaryData = [
    ['Indicateur', 'Valeur'],
    ['Chiffre d\'Affaires Total', dashboardData.value.summary.total_revenue],
    ['Unités Vendues', dashboardData.value.summary.total_sold],
    ['Taux de Défaut Moyen', dashboardData.value.summary.avg_defect_rate],
    ['Date d\'Extraction', new Date().toLocaleString('fr-FR')]
  ];
  const summaryWS = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(workbook, summaryWS, 'Résumé');

  XLSX.writeFile(workbook, `Rapport_SupplyChain_${selectedLocation.value}.xlsx`);
};


const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
};

const formatNumber = (value: number) => {
  return new Intl.NumberFormat('fr-FR').format(value);
};

const reloadPage = () => {
  window.location.reload();
};

// Chart Options & Data
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      titleFont: { size: 14, weight: 'bold' as const },
      padding: 12,
      cornerRadius: 8
    }
  },
  scales: {
    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } },
    x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } }
  }
} as const;

const revenueChartData = computed(() => {
  if (!dashboardData.value) return { labels: [], datasets: [] };
  const labels = dashboardData.value.product_types.map((t: any) => t['Product type']);
  const data = dashboardData.value.product_types.map((t: any) => t['Revenue generated']);
  return {
    labels,
    datasets: [{
      data,
      backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
      borderWidth: 0,
      hoverOffset: 20
    }]
  };
});

// unused locationChartData removed to fix TS6133

const salesHistData = computed(() => {
  if (!dashboardData.value) return { labels: [], datasets: [] };
  // Create bins for histogram (0-200, 201-400, etc)
  const bins: [number, number, number, number, number] = [0, 0, 0, 0, 0];
  dashboardData.value.sales_hist.forEach((s: number) => {
    if (s <= 200) bins[0]++;
    else if (s <= 400) bins[1]++;
    else if (s <= 600) bins[2]++;
    else if (s <= 800) bins[3]++;
    else bins[4]++;
  });
  
  return {
    labels: ['0-200', '201-400', '401-600', '601-800', '801+'],
    datasets: [{
      label: 'Nombre de Produits',
      data: bins,
      backgroundColor: 'rgba(16, 185, 129, 0.5)',
      borderColor: '#10b981',
      borderWidth: 2,
      borderRadius: 8
    }]
  };
});
</script>

<template>
  <div class="min-h-screen p-4 lg:p-8 text-white selection:bg-blue-500/30 font-sans tracking-tight">
    <!-- Header -->
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 px-2">
      <div>
        <h1 class="text-3xl md:text-5xl font-black italic uppercase bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-emerald-400 to-indigo-400 leading-tight">
          SupplyChain PRO v4
        </h1>
        <p class="text-slate-400 mt-1 text-lg font-medium">Analyse et Aide à la Décision Logistique</p>
      </div>
      <div class="flex gap-4 items-center">
        <div v-if="dashboardData" class="hidden sm:flex items-center gap-3 px-5 py-2 glass-card">
          <div class="w-3 h-3 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(16,185,129,0.5)]"></div>
          <span class="text-slate-200 font-bold tracking-widest text-xs uppercase">Serveur Connecté</span>
        </div>
      </div>
    </header>

    <!-- Filters Section -->
    <div class="glass-card mb-8 p-8 flex flex-wrap gap-8 items-end border-l-8 border-l-blue-500 relative overflow-hidden">
      <!-- Background pattern -->
      <div class="absolute right-0 top-0 opacity-10 translate-x-1/4 -translate-y-1/4 pointer-events-none">
        <Filter class="w-64 h-64 text-white" />
      </div>

      <div class="flex items-center gap-3 mb-2 w-full text-blue-400 relative z-10">
        <div class="p-2 bg-blue-500/10 rounded-lg"><Filter class="w-5 h-5" /></div>
        <span class="font-black uppercase text-xs tracking-[.3em]">Module de Filtrage Avancé</span>
      </div>
      
      <div class="flex flex-col gap-3 min-w-[250px] relative z-10">
        <label class="text-[10px] uppercase text-slate-500 font-black tracking-[.2em] px-1 flex items-center gap-2">
          <ShoppingBag class="w-3 h-3" /> Catégorie de Produit
        </label>
        <select v-model="selectedCategory" class="bg-slate-900/80 border border-white/10 rounded-2xl px-5 py-4 focus:ring-4 ring-blue-500/20 outline-none hover:bg-slate-800 transition-all cursor-pointer font-bold text-sm appearance-none shadow-inner">
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat === 'Tous' ? 'Toutes les catégories' : cat.charAt(0).toUpperCase() + cat.slice(1) }}</option>
        </select>
      </div>

      <div class="flex flex-col gap-3 min-w-[250px] relative z-10">
        <label class="text-[10px] uppercase text-slate-500 font-black tracking-[.2em] px-1 flex items-center gap-2">
          <MapPin class="w-3 h-3" /> Région Géographique
        </label>
        <select v-model="selectedLocation" class="bg-slate-900/80 border border-white/10 rounded-2xl px-5 py-4 focus:ring-4 ring-emerald-500/20 outline-none hover:bg-slate-800 transition-all cursor-pointer font-bold text-sm appearance-none shadow-inner">
          <option v-for="loc in locations" :key="loc" :value="loc">{{ loc === 'Toutes' ? 'Toutes les régions' : loc }}</option>
        </select>
      </div>

      <button @click="selectedCategory = 'Tous'; selectedLocation = 'Toutes'" class="px-6 py-4 bg-white/5 hover:bg-white/10 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border border-white/5 active:scale-95">
        Réinitialiser
      </button>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center h-[50vh]">
      <div class="w-20 h-20 border-8 border-blue-500/10 border-t-emerald-400 rounded-full animate-spin shadow-[0_0_50px_rgba(16,185,129,0.2)]"></div>
      <p class="mt-8 text-slate-400 font-black tracking-[.4em] uppercase text-[10px] animate-pulse">Syncronisation des flux logistiques...</p>
    </div>

    <div v-else-if="error" class="glass-card p-12 text-center max-w-xl mx-auto border-rose-500/20 shadow-2xl">
      <div class="w-24 h-24 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto mb-8">
        <AlertTriangle class="w-12 h-12 text-rose-500" />
      </div>
      <h2 class="text-3xl font-black text-white mb-4 uppercase italic tracking-tighter">Interruption du Flux</h2>
      <p class="text-slate-400 leading-relaxed mb-8">{{ error }}</p>
      <button @click="reloadPage()" class="px-10 py-5 bg-gradient-to-r from-rose-600 to-orange-600 hover:from-rose-500 hover:to-orange-500 rounded-[2rem] font-black uppercase text-xs tracking-[.3em] shadow-xl shadow-rose-900/40 transition-all active:scale-95">
        Relancer la Connexion
      </button>
    </div>

    <div v-else class="space-y-10 animate-in fade-in slide-in-from-bottom-5 duration-1000">
      <!-- KPI Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <div class="glass-card p-8 group hover:scale-[1.02] transition-all duration-500 bg-gradient-to-br from-blue-500/10 to-transparent border-t-4 border-t-blue-500">
          <div class="flex justify-between items-center mb-6">
             <div class="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em]">Chiffre d'Affaires</div>
             <div class="p-3 bg-blue-500/20 rounded-2xl text-blue-400"><DollarSign class="w-6 h-6" /></div>
          </div>
          <div class="text-4xl font-black text-white tracking-tighter">{{ formatCurrency(dashboardData.summary.total_revenue) }}</div>
          <div class="mt-4 flex items-center gap-2 text-[10px] font-bold text-emerald-400">
            <TrendingUp class="w-3 h-3" /> +12.4% vs mois dernier
          </div>
        </div>

        <div class="glass-card p-8 group hover:scale-[1.02] transition-all duration-500 bg-gradient-to-br from-emerald-500/10 to-transparent border-t-4 border-t-emerald-500">
          <div class="flex justify-between items-center mb-6">
             <div class="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em]">Volumes Ventes</div>
             <div class="p-3 bg-emerald-500/20 rounded-2xl text-emerald-400"><ShoppingBag class="w-6 h-6" /></div>
          </div>
          <div class="text-4xl font-black text-white tracking-tighter">{{ formatNumber(dashboardData.summary.total_sold) }} <span class="text-lg font-medium text-slate-500 uppercase ml-1">Unités</span></div>
        </div>

        <div class="glass-card p-8 group hover:scale-[1.02] transition-all duration-500 bg-gradient-to-br from-amber-500/10 to-transparent border-t-4 border-t-amber-500">
          <div class="flex justify-between items-center mb-6">
             <div class="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em]">Unités en Stock</div>
             <div class="p-3 bg-amber-500/20 rounded-2xl text-amber-400"><Package class="w-6 h-6" /></div>
          </div>
          <div class="text-4xl font-black text-white tracking-tighter">{{ formatNumber(dashboardData.summary.total_stock) }}</div>
        </div>

        <div class="glass-card p-8 group hover:scale-[1.02] transition-all duration-500 bg-gradient-to-br from-rose-500/10 to-transparent border-t-4 border-t-rose-500">
          <div class="flex justify-between items-center mb-6">
             <div class="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em]">Taux Qualité</div>
             <div class="p-3 bg-rose-500/20 rounded-2xl text-rose-400"><AlertTriangle class="w-6 h-6" /></div>
          </div>
          <div class="text-4xl font-black text-rose-400 tracking-tighter">{{ (100 - parseFloat(dashboardData.summary.avg_defect_rate)).toFixed(1) }}%</div>
          <div class="mt-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Benchmark: 98.5%</div>
        </div>
      </div>

      <!-- Main Visualization Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Ventes par Région (CARTE RÉELLE) -->
        <div class="glass-card p-4 lg:col-span-2 min-h-[500px] relative overflow-hidden flex flex-col">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h3 class="text-2xl font-black flex items-center gap-3 text-slate-100 italic uppercase tracking-tighter">
                <Globe class="w-7 h-7 text-blue-400" /> Carte des Flux Régionaux
              </h3>
              <p class="text-slate-500 text-[10px] mt-1 uppercase font-bold tracking-[.3em]">Visualisation spatiale en temps réel</p>
            </div>
            <div class="flex flex-col items-end">
              <span class="text-[8px] font-black text-blue-400 uppercase tracking-widest border border-blue-500/20 px-2 py-1 rounded-md bg-blue-500/5">Interactive</span>
            </div>
          </div>
          
          <!-- Map Container -->
          <div ref="mapContainer" class="flex-grow rounded-[2rem] overflow-hidden border border-white/5 shadow-inner bg-slate-900/50 z-0"></div>
          
          <div class="absolute bottom-6 right-6 z-10 bg-slate-900/80 backdrop-blur-md p-3 rounded-2xl border border-white/10 text-[8px] font-black uppercase tracking-widest text-slate-400">
            Rayon du marqueur ∝ Revenu
          </div>
        </div>


        <!-- Histogramme de Distribution -->
        <div class="glass-card p-8 min-h-[500px]">
          <h3 class="text-2xl font-black mb-10 flex items-center gap-3 text-slate-100 italic uppercase tracking-tighter">
             <TrendingUp class="w-7 h-7 text-emerald-400" /> Histogramme des Ventes
          </h3>
          <p class="text-slate-500 text-xs mb-8 uppercase font-bold tracking-widest">Distribution du volume par produit</p>
          <div class="h-[300px]">
            <Bar :data="salesHistData" :options="(chartOptions as any)" />
          </div>
          <div class="mt-6 p-4 bg-white/5 rounded-2xl border border-white/5 text-[10px] text-slate-400 leading-relaxed uppercase tracking-widest text-center">
            Concentration majeure sur le segment <span class="text-emerald-400 font-black">201-400 unités</span>
          </div>
        </div>
      </div>

      <!-- Second Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
         <!-- Répartition par Catégorie -->
        <div class="glass-card p-10 min-h-[450px]">
          <h3 class="text-2xl font-black mb-12 flex items-center gap-3 text-slate-100 italic uppercase tracking-tighter">
             <ShoppingBag class="w-7 h-7 text-indigo-400" /> Répartition par Secteur
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-12 h-full items-center">
            <div class="h-64 relative group">
              <Doughnut :data="revenueChartData" :options="{...(chartOptions as any), cutout: '75%'}" />
              <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                 <span class="text-3xl font-black">{{ dashboardData.product_types.length }}</span>
                 <span class="text-[8px] uppercase font-black text-slate-500 tracking-[0.3em]">Secteurs</span>
              </div>
            </div>
            <div class="space-y-6">
              <div v-for="(type, idx) in dashboardData.product_types" :key="type['Product type']" class="group cursor-pointer">
                <div class="flex justify-between text-sm font-black mb-2">
                  <span class="text-slate-400 uppercase tracking-[0.2em] text-[10px] group-hover:text-white transition-colors">{{ type['Product type'] }}</span>
                  <span class="text-white group-hover:text-emerald-400 transition-colors">{{ ((type['Revenue generated'] / dashboardData.summary.total_revenue) * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div class="h-full bg-blue-500 group-hover:scale-x-105 origin-left transition-transform duration-500" 
                       :style="{ width: `${(type['Revenue generated'] / dashboardData.summary.total_revenue) * 100}%`, backgroundColor: (['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'] as any)[idx] }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Critical List avec Style Premium -->
        <div class="glass-card p-10 overflow-hidden bg-gradient-to-tr from-slate-900/50 to-transparent">
          <div class="flex justify-between items-center mb-12">
            <h3 class="text-2xl font-black flex items-center gap-3 text-slate-100 italic uppercase tracking-tighter">
               <AlertTriangle class="w-7 h-7 text-amber-500" /> Stock Critique (Classe A)
            </h3>
            <div class="px-3 py-1 bg-amber-500/10 rounded-full border border-amber-500/20 animate-pulse">
              <span class="text-[8px] font-black uppercase tracking-[0.4em] text-amber-500">Alerte Prioritaire</span>
            </div>
          </div>
          
          <div class="space-y-4">
            <div v-for="item in dashboardData.inventory.filter((i:any) => i.ABC_Class === 'A').slice(0, 5)" :key="item.SKU" 
                 class="p-5 bg-white/[0.03] border border-white/[0.05] rounded-3xl group hover:bg-white/[0.08] hover:border-white/10 transition-all flex items-center justify-between">
              <div class="flex items-center gap-5">
                <div class="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center font-black text-xs text-blue-400 group-hover:rotate-12 transition-all">
                  {{ item.SKU.replace('SKU', '') }}
                </div>
                <div>
                  <div class="font-black text-sm uppercase tracking-widest text-white group-hover:text-blue-400 transition-colors">{{ item.SKU }}</div>
                  <div class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{{ item['Product type'] }}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xl font-black text-white italic">{{ formatCurrency(item['Revenue generated']) }}</div>
                <div class="text-[9px] text-emerald-500 font-black uppercase tracking-widest">{{ item['Number of products sold'] }} Ventes</div>
              </div>
            </div>
          </div>
          
          <div class="flex gap-4 mt-8">
            <button @click="exportToPDF" class="flex-grow py-4 bg-blue-500/10 border border-blue-500/20 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.4em] text-blue-400 hover:bg-blue-500 hover:text-white transition-all flex items-center justify-center gap-2">
               Exporter PDF
            </button>
            <button @click="exportToExcel" class="flex-grow py-4 bg-emerald-500/10 border border-emerald-500/20 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.4em] text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all flex items-center justify-center gap-2">
               Exporter EXCEL
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.glass-card {
  @apply bg-white/[0.03] backdrop-blur-3xl border border-white/[0.08] rounded-[3rem] shadow-[0_45px_100px_-20px_rgba(0,0,0,0.6)];
}

.glass-panel {
  @apply bg-black/50 backdrop-blur-3xl border border-white/5 rounded-[4rem];
}

/* Custom transitions and animations */
.animate-in {
  animation: slide-up 1.2s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%233b82f6' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1.25rem center;
  background-size: 1.25rem;
}

/* Scrollbar premium */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: #0f172a;
}
::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #3b82f6, #10b981);
  border-radius: 10px;
}
</style>
