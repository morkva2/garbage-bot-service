import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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

interface ClientViewProps {
  clientOrders: Order[];
  newOrder: {
    address: string;
    description: string;
    price: string;
  };
  onNewOrderChange: (field: string, value: string) => void;
  onCreateOrder: () => void;
  onRateOrder: (orderId: string, rating: number, review: string) => void;
  onBack: () => void;
}

const ClientView = ({ 
  clientOrders, 
  newOrder, 
  onNewOrderChange, 
  onCreateOrder, 
  onRateOrder, 
  onBack 
}: ClientViewProps) => {
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
              <Icon name="User" size={16} className="mr-1" />
              Клиент
            </Badge>
          </div>
        </div>

        <Tabs defaultValue="create" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-4">
            <TabsTrigger value="create">Создать</TabsTrigger>
            <TabsTrigger value="active">Активные</TabsTrigger>
            <TabsTrigger value="history">История</TabsTrigger>
            <TabsTrigger value="settings">Настройки</TabsTrigger>
          </TabsList>

          <TabsContent value="create">
            <Card>
              <CardHeader>
                <CardTitle>Новый заказ</CardTitle>
                <CardDescription>Создайте заявку на вывоз мусора</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="address">Адрес</Label>
                  <Input 
                    id="address" 
                    placeholder="ул. Ленина, д. 45, кв. 12"
                    value={newOrder.address}
                    onChange={(e) => onNewOrderChange('address', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Описание</Label>
                  <Textarea 
                    id="description" 
                    placeholder="Что нужно вывезти?"
                    value={newOrder.description}
                    onChange={(e) => onNewOrderChange('description', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Цена (₽)</Label>
                  <Input 
                    id="price" 
                    type="number"
                    placeholder="1500"
                    value={newOrder.price}
                    onChange={(e) => onNewOrderChange('price', e.target.value)}
                  />
                </div>
                <Button className="w-full" onClick={onCreateOrder}>
                  <Icon name="Plus" size={18} className="mr-2" />
                  Создать заказ
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="active" className="space-y-4">
            {clientOrders.filter(o => o.status !== 'completed').map((order) => (
              <Card key={order.id} className="hover-scale">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{order.address}</CardTitle>
                      <CardDescription>{order.description}</CardDescription>
                    </div>
                    <Badge variant={order.status === 'pending' ? 'secondary' : 'default'}>
                      {order.status === 'pending' ? 'В поиске курьера' : 'Принят'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-center">
                    <span className="text-2xl font-bold text-primary">{order.price} ₽</span>
                    {order.courierName && (
                      <div className="text-sm text-muted-foreground">
                        <Icon name="User" size={16} className="inline mr-1" />
                        Курьер: {order.courierName}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {clientOrders.filter(o => o.status !== 'completed').length === 0 && (
              <Card>
                <CardContent className="text-center py-12 text-muted-foreground">
                  <Icon name="PackageOpen" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Нет активных заказов</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            {clientOrders.filter(o => o.status === 'completed').map((order) => (
              <Card key={order.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{order.address}</CardTitle>
                      <CardDescription>{order.description}</CardDescription>
                    </div>
                    <Badge variant="outline" className="text-green-600">Завершён</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">{order.price} ₽</span>
                  </div>
                  {!order.rating && (
                    <div className="space-y-2 pt-2 border-t">
                      <Label>Оцените курьера</Label>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button key={star} onClick={() => {
                            const review = prompt('Оставьте отзыв (необязательно)');
                            onRateOrder(order.id, star, review || '');
                          }}>
                            <Icon name="Star" size={24} className="text-yellow-500 hover:fill-current cursor-pointer" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
            {clientOrders.filter(o => o.status === 'completed').length === 0 && (
              <Card>
                <CardContent className="text-center py-12 text-muted-foreground">
                  <Icon name="Archive" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>История заказов пуста</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>Настройки</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Способ оплаты</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите способ оплаты" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="card">Банковская карта</SelectItem>
                      <SelectItem value="cash">Наличные</SelectItem>
                      <SelectItem value="sbp">СБП</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="space-y-2">
                  <Label>Подписка</Label>
                  <div className="bg-primary/10 p-4 rounded-lg">
                    <p className="font-semibold">Базовый план</p>
                    <p className="text-sm text-muted-foreground">Без комиссии за первые 3 заказа</p>
                  </div>
                </div>
                <Button variant="outline" className="w-full">
                  <Icon name="MessageCircle" size={18} className="mr-2" />
                  Связаться с поддержкой
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ClientView;
