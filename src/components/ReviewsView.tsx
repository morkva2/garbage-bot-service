import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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

interface ReviewsViewProps {
  completedOrders: Order[];
  onBack: () => void;
}

const ReviewsView = ({ completedOrders, onBack }: ReviewsViewProps) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 p-4">
      <div className="max-w-4xl mx-auto animate-fade-in">
        <Button variant="ghost" onClick={onBack} className="mb-6">
          <Icon name="ArrowLeft" size={20} className="mr-2" />
          Назад
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Отзывы клиентов</CardTitle>
            <CardDescription>Реальные оценки нашей работы</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {completedOrders.filter(o => o.rating).map((order) => (
              <div key={order.id} className="border-b pb-4 last:border-b-0">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center gap-1 text-yellow-500">
                    {[...Array(5)].map((_, i) => (
                      <Icon key={i} name="Star" size={16} className={i < (order.rating || 0) ? "fill-current" : "opacity-30"} />
                    ))}
                  </div>
                  <span className="text-sm text-muted-foreground">{order.clientName}</span>
                </div>
                {order.review && <p className="text-sm">{order.review}</p>}
              </div>
            ))}
            {completedOrders.filter(o => o.rating).length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <Icon name="MessageSquare" size={48} className="mx-auto mb-4 opacity-50" />
                <p>Отзывов пока нет</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ReviewsView;
