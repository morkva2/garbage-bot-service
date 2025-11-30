import { useState } from 'react';
import { toast } from 'sonner';
import MainMenu from '@/components/MainMenu';
import CourierView from '@/components/CourierView';
import ClientView from '@/components/ClientView';
import ReviewsView from '@/components/ReviewsView';

type UserRole = 'none' | 'client' | 'courier';
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

const Index = () => {
  const [userRole, setUserRole] = useState<UserRole>('none');
  const [view, setView] = useState<string>('main');
  
  const [orders, setOrders] = useState<Order[]>([
    {
      id: '1',
      clientName: 'Иван Петров',
      address: 'ул. Ленина, д. 45, кв. 12',
      description: 'Вывоз строительного мусора (3 мешка)',
      price: 1500,
      status: 'pending',
    },
    {
      id: '2',
      clientName: 'Мария Сидорова',
      address: 'пр. Мира, д. 78, кв. 5',
      description: 'Старая мебель (диван, стол)',
      price: 2500,
      status: 'pending',
    },
  ]);

  const [courierOrders, setCourierOrders] = useState<Order[]>([]);
  const [completedOrders, setCompletedOrders] = useState<Order[]>([]);
  const [clientOrders, setClientOrders] = useState<Order[]>([]);

  const [newOrder, setNewOrder] = useState({
    address: '',
    description: '',
    price: '',
  });

  const handleCreateOrder = () => {
    if (!newOrder.address || !newOrder.description || !newOrder.price) {
      toast.error('Заполните все поля');
      return;
    }

    const order: Order = {
      id: Date.now().toString(),
      clientName: 'Вы',
      address: newOrder.address,
      description: newOrder.description,
      price: Number(newOrder.price),
      status: 'pending',
    };

    setOrders([...orders, order]);
    setClientOrders([...clientOrders, order]);
    setNewOrder({ address: '', description: '', price: '' });
    toast.success('Заказ создан');
    setView('client-active');
  };

  const handleAcceptOrder = (orderId: string) => {
    const order = orders.find(o => o.id === orderId);
    if (order) {
      const acceptedOrder = { ...order, status: 'accepted' as OrderStatus, courierName: 'Вы' };
      setOrders(orders.filter(o => o.id !== orderId));
      setCourierOrders([...courierOrders, acceptedOrder]);
      toast.success('Заказ принят');
    }
  };

  const handleCompleteOrder = (orderId: string) => {
    const order = courierOrders.find(o => o.id === orderId);
    if (order) {
      const completedOrder = { ...order, status: 'completed' as OrderStatus };
      setCourierOrders(courierOrders.filter(o => o.id !== orderId));
      setCompletedOrders([...completedOrders, completedOrder]);
      toast.success('Заказ завершён');
    }
  };

  const handleRateOrder = (orderId: string, rating: number, review: string) => {
    setCompletedOrders(completedOrders.map(o => 
      o.id === orderId ? { ...o, rating, review } : o
    ));
    toast.success('Отзыв отправлен');
  };

  const handleNewOrderChange = (field: string, value: string) => {
    setNewOrder({ ...newOrder, [field]: value });
  };

  return (
    <>
      {view === 'main' && (
        <MainMenu
          onSelectCourier={() => { setUserRole('courier'); setView('courier-menu'); }}
          onSelectClient={() => { setUserRole('client'); setView('client-menu'); }}
          onShowReviews={() => setView('reviews')}
        />
      )}
      {view === 'courier-menu' && (
        <CourierView
          orders={orders}
          courierOrders={courierOrders}
          completedOrders={completedOrders}
          onAcceptOrder={handleAcceptOrder}
          onCompleteOrder={handleCompleteOrder}
          onBack={() => { setView('main'); setUserRole('none'); }}
        />
      )}
      {view === 'client-menu' && (
        <ClientView
          clientOrders={clientOrders}
          newOrder={newOrder}
          onNewOrderChange={handleNewOrderChange}
          onCreateOrder={handleCreateOrder}
          onRateOrder={handleRateOrder}
          onBack={() => { setView('main'); setUserRole('none'); }}
        />
      )}
      {view === 'reviews' && (
        <ReviewsView
          completedOrders={completedOrders}
          onBack={() => setView('main')}
        />
      )}
    </>
  );
};

export default Index;
