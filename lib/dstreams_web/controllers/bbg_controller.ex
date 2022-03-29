defmodule DstreamsWeb.Api.BbgController do
  use DstreamsWeb, :controller

  def index(conn, _params) do
    random_string = for _ <- 1..10, into: "", do: <<Enum.random('0123456789abcdef')>>
    json(conn, %{data: %{live: [random_string, "USDZAR Curncy", "USDTRY Curncy"]}})
  end

  def show(conn, params) do

  end

  def create(conn, params) do
    IO.puts("-----------")
    conn
    |> put_status(:created)
    |> put_resp_header("location", " ") # XXX not working TODO
  end

end
      




