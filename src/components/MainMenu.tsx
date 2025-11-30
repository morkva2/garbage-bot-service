import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import Icon from '@/components/ui/icon';

interface MainMenuProps {
  onSelectCourier: () => void;
  onSelectClient: () => void;
  onShowReviews: () => void;
}

const MainMenu = ({ onSelectCourier, onSelectClient, onShowReviews }: MainMenuProps) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl animate-fade-in">
        <CardHeader className="text-center space-y-2 pb-8">
          <div className="mx-auto bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mb-4">
            <Icon name="Truck" size={40} className="text-primary" />
          </div>
          <CardTitle className="text-3xl font-bold text-primary">Экономь время</CardTitle>
          <CardDescription className="text-base">Курьерская служба вывоза мусора</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            className="w-full h-14 text-lg hover-scale" 
            onClick={onSelectCourier}
          >
            <Icon name="Briefcase" size={20} className="mr-2" />
            Стать курьером
          </Button>
          <Button 
            className="w-full h-14 text-lg hover-scale" 
            variant="outline"
            onClick={onSelectClient}
          >
            <Icon name="User" size={20} className="mr-2" />
            Для клиентов
          </Button>
          <Separator className="my-4" />
          <Button 
            className="w-full h-12 hover-scale" 
            variant="ghost"
            onClick={onShowReviews}
          >
            <Icon name="Star" size={20} className="mr-2" />
            Отзывы
          </Button>
          <Button 
            className="w-full h-12 hover-scale" 
            variant="ghost"
            onClick={() => window.open('https://t.me/support', '_blank')}
          >
            <Icon name="MessageCircle" size={20} className="mr-2" />
            Поддержка
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default MainMenu;
