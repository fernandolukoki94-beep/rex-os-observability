import { Route, Switch } from "wouter";
import RexLanding from "./pages/RexLanding";
import RexOperations from "./pages/RexOperations";

export default function App() {
  return (
    <Switch>
      <Route path="/rex" component={RexOperations} />
      <Route path="/operations" component={RexOperations} />
      <Route path="/" component={RexLanding} />
      <Route component={RexLanding} />
    </Switch>
  );
}
