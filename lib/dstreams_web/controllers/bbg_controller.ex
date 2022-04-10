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
    IO.inspect params
    conn
    |> put_status(:ok)
    |> send_resp(200, "ok")
  end

  def test_send(conn, _params) do
    json(conn, %{data: %{live: ["test_recieved"]}})
  end

end
      




