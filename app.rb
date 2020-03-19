require 'erubi'
require './showquota'
require './squeue'
require './myproject'

set :erb, :escape_html => true

if development?
  require 'sinatra/reloader'
  also_reload './showquota.rb'
  also_reload './squeue.rb'
  also_reload './myproject.rb'
end

helpers do
  def dashboard_title
    "Open OnDemand"
  end

  def dashboard_url
    "/pun/sys/dashboard/"
  end

  def title
    "Your Dashboard"
  end
end

# Define a route at the root '/' of the app.
get '/' do

  @showquota = ShowQuota.new
  @quota, @error = @showquota.exec

  @squeue = Squeue.new
  @jobs, @error = @squeue.exec

  @myproject = MyProject.new
  @allocations = @myproject.exec
  # Render the view
  erb :index
end