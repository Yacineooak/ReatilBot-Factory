import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts'
import { 
  MessageSquare, ShoppingCart, Shield, Package, TrendingUp, TrendingDown,
  AlertTriangle, CheckCircle, Clock, Users, DollarSign, Activity
} from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:5001/api'

function App() {
  const [dashboardData, setDashboardData] = useState(null)
  const [conversationTrends, setConversationTrends] = useState(null)
  const [revenueTrends, setRevenueTrends] = useState(null)
  const [riskAnalysis, setRiskAnalysis] = useState(null)
  const [inventoryInsights, setInventoryInsights] = useState(null)
  const [performanceKPIs, setPerformanceKPIs] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch all analytics data
      const [dashboard, conversations, revenue, risk, inventory, kpis] = await Promise.all([
        fetch(`${API_BASE_URL}/analytics/dashboard`).then(res => res.json()),
        fetch(`${API_BASE_URL}/analytics/conversations/trends`).then(res => res.json()),
        fetch(`${API_BASE_URL}/analytics/revenue/trends`).then(res => res.json()),
        fetch(`${API_BASE_URL}/analytics/risk/analysis`).then(res => res.json()),
        fetch(`${API_BASE_URL}/analytics/inventory/insights`).then(res => res.json()),
        fetch(`${API_BASE_URL}/analytics/performance/kpis`).then(res => res.json())
      ])

      setDashboardData(dashboard)
      setConversationTrends(conversations)
      setRevenueTrends(revenue)
      setRiskAnalysis(risk)
      setInventoryInsights(inventory)
      setPerformanceKPIs(kpis)
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'bg-green-500'
      case 'warning': return 'bg-yellow-500'
      case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'good': return <CheckCircle className="h-4 w-4" />
      case 'warning': return <AlertTriangle className="h-4 w-4" />
      case 'critical': return <AlertTriangle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement du tableau de bord...</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-2xl font-bold text-gray-900">🤖 RetailBot Factory</h1>
                  <p className="text-sm text-gray-500">Tableau de Bord Analytique</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Button onClick={fetchDashboardData} variant="outline">
                  <Activity className="h-4 w-4 mr-2" />
                  Actualiser
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={
              <DashboardContent 
                dashboardData={dashboardData}
                conversationTrends={conversationTrends}
                revenueTrends={revenueTrends}
                riskAnalysis={riskAnalysis}
                inventoryInsights={inventoryInsights}
                performanceKPIs={performanceKPIs}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            } />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

function DashboardContent({ 
  dashboardData, 
  conversationTrends, 
  revenueTrends, 
  riskAnalysis, 
  inventoryInsights, 
  performanceKPIs,
  getStatusColor,
  getStatusIcon 
}) {
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  return (
    <div className="px-4 py-6 sm:px-0">
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="conversations">Conversations</TabsTrigger>
          <TabsTrigger value="revenue">Revenus</TabsTrigger>
          <TabsTrigger value="risk">Risques</TabsTrigger>
          <TabsTrigger value="inventory">Inventaire</TabsTrigger>
        </TabsList>

        {/* Vue d'ensemble */}
        <TabsContent value="overview" className="space-y-6">
          {/* KPIs principaux */}
          {performanceKPIs && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(performanceKPIs.kpis).map(([key, kpi]) => (
                <Card key={key}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{kpi.description}</CardTitle>
                    <div className={`p-2 rounded-full ${getStatusColor(kpi.status)}`}>
                      {getStatusIcon(kpi.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {kpi.value} {kpi.unit}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Objectif: {kpi.target} {kpi.unit}
                    </p>
                    <Badge variant={kpi.status === 'good' ? 'default' : kpi.status === 'warning' ? 'secondary' : 'destructive'}>
                      {kpi.status === 'good' ? 'Excellent' : kpi.status === 'warning' ? 'Attention' : 'Critique'}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Métriques principales */}
          {dashboardData && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversations</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.conversations.total}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.conversations.avg_messages_per_conversation} messages/conv
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Paniers Récupérés</CardTitle>
                  <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.cart_recovery.recovery_rate}%</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.cart_recovery.recovered}/{dashboardData.cart_recovery.total_abandoned} paniers
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Commandes COD</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.cod_management.total_orders}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.cod_management.risk_percentage}% à haut risque
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Santé Inventaire</CardTitle>
                  <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.inventory.stock_health_percentage}%</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.inventory.active_alerts} alertes actives
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Conversations */}
        <TabsContent value="conversations" className="space-y-6">
          {conversationTrends && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tendances des Conversations</CardTitle>
                  <CardDescription>Évolution quotidienne des conversations</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={conversationTrends.daily_conversations}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Intentions Principales</CardTitle>
                  <CardDescription>Top 10 des intentions détectées</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={conversationTrends.top_intents}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="intent" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Revenus */}
        <TabsContent value="revenue" className="space-y-6">
          {revenueTrends && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Revenus Récupérés</CardTitle>
                  <CardDescription>Revenus générés par la récupération de paniers</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={revenueTrends.daily_revenue}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Area type="monotone" dataKey="revenue" stroke="#82ca9d" fill="#82ca9d" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance par Canal</CardTitle>
                  <CardDescription>Efficacité des canaux de récupération</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={revenueTrends.channel_performance}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="channel" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="conversion_rate" fill="#ffc658" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Risques */}
        <TabsContent value="risk" className="space-y-6">
          {riskAnalysis && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Distribution des Risques</CardTitle>
                  <CardDescription>Répartition des commandes par niveau de risque</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={riskAnalysis.risk_distribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ risk_level, count }) => `${risk_level}: ${count}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {riskAnalysis.risk_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Villes à Risque</CardTitle>
                  <CardDescription>Top 10 des villes avec le plus haut risque</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {riskAnalysis.top_risk_cities.slice(0, 5).map((city, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="font-medium">{city.city}</span>
                        <div className="flex items-center space-x-2">
                          <Badge variant={city.risk_percentage > 50 ? 'destructive' : city.risk_percentage > 25 ? 'secondary' : 'default'}>
                            {city.risk_percentage}%
                          </Badge>
                          <span className="text-sm text-gray-500">{city.total_orders} commandes</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Inventaire */}
        <TabsContent value="inventory" className="space-y-6">
          {inventoryInsights && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Articles à Stock Faible</CardTitle>
                  <CardDescription>Articles nécessitant un réapprovisionnement</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {inventoryInsights.low_stock_items.slice(0, 5).map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div>
                          <span className="font-medium">{item.product_name}</span>
                          <p className="text-sm text-gray-500">{item.category}</p>
                        </div>
                        <div className="text-right">
                          <Badge variant="destructive">{item.current_stock}</Badge>
                          <p className="text-xs text-gray-500">Min: {item.min_threshold}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Distribution par Catégorie</CardTitle>
                  <CardDescription>Répartition de l'inventaire par catégorie</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={inventoryInsights.category_distribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ category, count }) => `${category}: ${count}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {inventoryInsights.category_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default App

