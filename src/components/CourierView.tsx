import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';

type OrderStatus = 'pending' | 'accepted' | 'completed' | 'cancelled';

interface Order {
  id: string;
  clientName: string;
  address: string;
  description: string;
  price: number;
  status: OrderStatus;
  courierName?: string;
  rating?: number;
  review?: string;
}

interface CourierViewProps {
  orders: Order[];
  courierOrders: Order[];
  completedOrders: Order[];
  onAcceptOrder: (orderId: string) => void;
  onCompleteOrder: (orderId: string) => void;
  onBack: () => void;
}

const CourierView = ({ 
  orders, 
  courierOrders, 
  completedOrders, 
  onAcceptOrder, 
  onCompleteOrder, 
  onBack 
}: CourierViewProps) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 p-4">
      <div className="max-w-4xl mx-auto space-y-4 animate-fade-in">
        <div className="flex items-center justify-between mb-6">
          <Button variant="ghost" onClick={onBack}>
            <Icon name="ArrowLeft" size={20} className="mr-2" />
            Назад
          </Button>
          <div className="flex items-center gap-2">
            <Badge variant="default" className="text-sm px-3 py-1">
              <Icon name="Briefcase" size={16} className="mr-1" />
              Курьер
            </Badge>
          </div>
        </div>

        <Tabs defaultValue="available" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-4">
            <TabsTrigger value="available">Доступные</TabsTrigger>
            <TabsTrigger value="current">Текущие</TabsTrigger>
            <TabsTrigger value="history">История</TabsTrigger>
            <TabsTrigger value="stats">Статистика</TabsTrigger>
          </TabsList>

          <TabsContent value="available" className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} className="hover-scale">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{order.address}</CardTitle>
                      <CardDescription>{order.description}</CardDescription>
                    </div>
                    <Badge className="bg-green-500 text-white">{order.price} ₽</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button className="w-full" onClick={() => onAcceptOrder(order.id)}>
                    <Icon name="Check" size={18} className="mr-2" />
                    Принять заказ
                  </Button>
                </CardContent>
              </Card>
            ))}
            {orders.length === 0 && (
              <Card>
                <CardContent className="text-center py-12 text-muted-foreground">
                  <Icon name="Package" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Нет доступных заказов</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="current" className="space-y-4">
            {courierOrders.map((order) => (
              <Card key={order.id} className="hover-scale border-primary">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{order.address}</CardTitle>
                      <CardDescription>{order.description}</CardDescription>
                    </div>
                    <Badge className="bg-blue-500 text-white">{order.price} ₽</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center text-sm text-muted-foreground">
                    <Icon name="User" size={16} className="mr-2" />
                    {order.clientName}
                  </div>
                  <Button className="w-full" onClick={() => onCompleteOrder(order.id)}>
                    <Icon name="CheckCircle2" size={18} className="mr-2" />
                    Завершить заказ
                  </Button>
                </CardContent>
              </Card>
            ))}
            {courierOrders.length === 0 && (
              <Card>
                <CardContent className="text-center py-12 text-muted-foreground">
                  <Icon name="ClipboardList" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Нет текущих заказов</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            {completedOrders.map((order) => (
              <Card key={order.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{order.address}</CardTitle>
                      <CardDescription>{order.description}</CardDescription>
                    </div>
                    <Badge variant="outline" className="text-green-600">{order.price} ₽</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {order.rating && (
                    <div className="flex items-center gap-1 text-sm text-yellow-500">
                      {[...Array(5)].map((_, i) => (
                        <Icon key={i} name={i < order.rating! ? "Star" : "Star"} size={16} className={i < order.rating! ? "fill-current" : "opacity-30"} />
                      ))}
                      {order.review && <span className="ml-2 text-muted-foreground">"{order.review}"</span>}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
            {completedOrders.length === 0 && (
              <Card>
                <CardContent className="text-center py-12 text-muted-foreground">
                  <Icon name="History" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>История заказов пуста</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle>Финансовая статистика</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-primary/10 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">Всего заказов</p>
                    <p className="text-3xl font-bold text-primary">{completedOrders.length}</p>
                  </div>
                  <div className="bg-green-500/10 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">Заработано</p>
                    <p className="text-3xl font-bold text-green-600">
                      {completedOrders.reduce((sum, o) => sum + o.price, 0)} ₽
                    </p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Средний чек</span>
                    <span className="font-semibold">
                      {completedOrders.length > 0 
                        ? Math.round(completedOrders.reduce((sum, o) => sum + o.price, 0) / completedOrders.length)
                        : 0} ₽
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Средний рейтинг</span>
                    <div className="flex items-center gap-1">
                      <Icon name="Star" size={16} className="text-yellow-500 fill-current" />
                      <span className="font-semibold">
                        {completedOrders.length > 0
                          ? (completedOrders.filter(o => o.rating).reduce((sum, o) => sum + (o.rating || 0), 0) / completedOrders.filter(o => o.rating).length || 0).toFixed(1)
                          : '0.0'}
                      </span>
                    </div>
                  </div>
                </div>
                <Separator />
                <Button className="w-full" variant="outline">
                  <Icon name="DollarSign" size={18} className="mr-2" />
                  Вывод средств
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CourierView;
